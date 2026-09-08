"""
Two separate client classes, because these are two completely different
UniFi APIs with different stability guarantees. NEVER mix them - that was
the key lesson from the architecture discussion: Integration API = stable/
official, v2 API = fragile/unofficial.
"""
import logging

import requests
from requests.exceptions import RequestException

logger = logging.getLogger('netbox_unifi_aio')


class UnifiAPIError(Exception):
    """Base exception for all UniFi API errors. Sync jobs catch this."""
    pass


class UnifiIntegrationClient:
    """
    Official Integration API v1 (/integration/v1/*). API-key auth.
    This is the source network/ relies on - see developer.ui.com.
    """

    def __init__(self, base_url: str, api_key: str, verify_tls: bool = False, timeout: int = 15):
        self.base_url = base_url.rstrip('/')
        self.verify_tls = verify_tls
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Accept': 'application/json',
        })
        if not verify_tls:
            # Home-network UCK/UDM units usually don't have a certificate signed
            # by a real CA. Suppress the warning, but deliberately and visibly in logs.
            requests.packages.urllib3.disable_warnings()
            logger.debug('TLS verification disabled for %s', self.base_url)

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f'{self.base_url}{path}'
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout, verify=self.verify_tls)
            resp.raise_for_status()
            return resp.json()
        except RequestException as exc:
            raise UnifiAPIError(f'GET {url} failed: {exc}') from exc

    def list_sites(self) -> list[dict]:
        data = self._get('/proxy/network/integration/v1/sites')
        return data.get('data', [])

    def list_devices(self, site_id: str) -> list[dict]:
        devices, offset, limit = [], 0, 100
        while True:
            data = self._get(
                f'/proxy/network/integration/v1/sites/{site_id}/devices',
                params={'offset': offset, 'limit': limit},
            )
            batch = data.get('data', [])
            devices.extend(batch)
            if len(batch) < limit:
                break
            offset += limit
        return devices

    def list_clients(self, site_id: str) -> list[dict]:
        clients, offset, limit = [], 0, 100
        while True:
            data = self._get(
                f'/proxy/network/integration/v1/sites/{site_id}/clients',
                params={'offset': offset, 'limit': limit},
            )
            batch = data.get('data', [])
            clients.extend(batch)
            if len(batch) < limit:
                break
            offset += limit
        return clients


class UnifiDesignClient:
    """
    Unofficial v2 controller API (/v2/api/*). Session-cookie auth
    (login with username/password, no API key possible).

    WARNING: This API is NOT documented and can change with every UniFi
    firmware update. Every method deliberately catches errors individually
    so a broken endpoint doesn't take down the entire sync.
    """

    def __init__(self, base_url: str, username: str, password: str,
                 verify_tls: bool = False, timeout: int = 15):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_tls = verify_tls
        self.timeout = timeout
        self.session = requests.Session()
        self._logged_in = False
        if not verify_tls:
            requests.packages.urllib3.disable_warnings()

    def login(self):
        url = f'{self.base_url}/api/auth/login'
        try:
            resp = self.session.post(
                url,
                json={'username': self.username, 'password': self.password},
                timeout=self.timeout,
                verify=self.verify_tls,
            )
            resp.raise_for_status()
            self._logged_in = True
            logger.info('UniFi Design login successful for %s', self.base_url)
        except RequestException as exc:
            raise UnifiAPIError(
                f'Login to {self.base_url} failed - check credentials, '
                f'or has the login endpoint changed? ({exc})'
            ) from exc

    def _ensure_login(self):
        if not self._logged_in:
            self.login()

    def _get(self, path: str) -> dict | list:
        """
        GET with a single automatic re-login retry on an expired session
        cookie. The v2 API runs on embedded controllers that can drop the
        session server-side between requests, and the client's own
        _logged_in flag has no way to detect that on its own.
        """
        self._ensure_login()
        url = f'{self.base_url}{path}'
        try:
            resp = self.session.get(url, timeout=self.timeout, verify=self.verify_tls)
            if resp.status_code in (401, 403):
                logger.info('UniFi Design session expired for %s, re-authenticating', self.base_url)
                self._logged_in = False
                self._ensure_login()
                resp = self.session.get(url, timeout=self.timeout, verify=self.verify_tls)
            resp.raise_for_status()
            return resp.json()
        except RequestException as exc:
            raise UnifiAPIError(f'GET {url} failed: {exc}') from exc

    def get_maps(self, site: str) -> list[dict]:
        """
        Returns the floorplan maps created in the UniFi Design section.
        The structure (image reference, device positions) is NOT officially
        documented - verify against a real response before production use
        and adjust this method if needed.
        """
        return self._get(f'/proxy/network/v2/api/site/{site}/maps')

    def get_walls(self, site: str) -> list[dict]:
        return self._get(f'/proxy/network/v2/api/site/{site}/walls')
