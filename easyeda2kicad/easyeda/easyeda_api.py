# Global imports
import logging

import requests
from requests import RequestException

from easyeda2kicad import __version__

API_ENDPOINT = "https://easyeda.com/api/products/{lcsc_id}/components?version=6.4.19.5"
ENDPOINT_3D_MODEL = "https://modules.easyeda.com/3dmodel/{uuid}"
ENDPOINT_3D_MODEL_STEP = "https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/{uuid}"
# ENDPOINT_3D_MODEL_STEP found in https://modules.lceda.cn/smt-gl-engine/0.8.22.6032922c/smt-gl-engine.js : points to the bucket containing the step files.

# ------------------------------------------------------------


class EasyedaApi:
    def __init__(self) -> None:
        self.last_error_message = None
        self.last_error_code = None
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://easyeda.com/",
            # EasyEDA currently rejects the old custom user agent with CloudFront 403s.
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
        }

    def get_info_from_easyeda_api(self, lcsc_id: str) -> dict:
        self.last_error_message = None
        self.last_error_code = None
        try:
            r = requests.get(
                url=API_ENDPOINT.format(lcsc_id=lcsc_id),
                headers=self.headers,
                timeout=30,
            )
            r.raise_for_status()
        except RequestException as exc:
            self.last_error_message = str(exc)
            logging.error(f"EasyEDA API request failed for part {lcsc_id}: {exc}")
            return {}

        try:
            api_response = r.json()
        except ValueError:
            self.last_error_message = "EasyEDA returned an invalid response."
            logging.error(
                "EasyEDA API returned a non-JSON response for part %s "
                "(status=%s, content-type=%s, body-start=%r)",
                lcsc_id,
                r.status_code,
                r.headers.get("content-type"),
                r.text[:200],
            )
            return {}

        if not api_response or (
            "code" in api_response and api_response["success"] is False
        ):
            self.last_error_code = api_response.get("code")
            self.last_error_message = api_response.get("message") or "Unknown EasyEDA API error."
            logging.error(
                "EasyEDA API reported an error for part %s: code=%s message=%s",
                lcsc_id,
                self.last_error_code,
                self.last_error_message,
            )
            logging.debug(f"{api_response}")
            return {}

        return api_response

    def get_cad_data_of_component(self, lcsc_id: str) -> dict:
        cp_cad_info = self.get_info_from_easyeda_api(lcsc_id=lcsc_id)
        if cp_cad_info == {}:
            return {}
        return cp_cad_info["result"]

    def get_raw_3d_model_obj(self, uuid: str) -> str:
        r = requests.get(
            url=ENDPOINT_3D_MODEL.format(uuid=uuid),
            headers={"User-Agent": self.headers["User-Agent"]},
            timeout=30,
        )
        if r.status_code != requests.codes.ok:
            logging.error(f"No raw 3D model data found for uuid:{uuid} on easyeda")
            return None
        return r.content.decode()

    def get_step_3d_model(self, uuid: str) -> bytes:
        r = requests.get(
            url=ENDPOINT_3D_MODEL_STEP.format(uuid=uuid),
            headers={"User-Agent": self.headers["User-Agent"]},
            timeout=30,
        )
        if r.status_code != requests.codes.ok:
            logging.error(f"No step 3D model data found for uuid:{uuid} on easyeda")
            return None
        return r.content
