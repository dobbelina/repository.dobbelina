import requests


class FlareSolverrManager:
    def __init__(self, flaresolverr_url=None):
        self.session = requests.session()
        self.flaresolverr_url = flaresolverr_url or "http://localhost:8191/v1"

        # We clear all sessions to make sure to not have conflicts
        self.clear_flaresolverr_sessions()

        session_create_request = {"cmd": "sessions.create"}
        session_create_response = requests.post(
            self.flaresolverr_url, json=session_create_request
        )

        self.flaresolverr_session = session_create_response.json().get("session")

    def clear_flaresolverr_sessions(self):
        # Get session list
        session_list_request = {"cmd": "sessions.list"}
        session_list_response = requests.post(
            self.flaresolverr_url, json=session_list_request
        )

        sessions = session_list_response.json().get("sessions")

        # Clear each session
        if sessions:
            for session_id in sessions:
                session_destroy_request = {"cmd": "sessions.destroy", "session": session_id}
                requests.post(self.flaresolverr_url, json=session_destroy_request)

    def request(self, url, method="GET", cookies=None, tries=3):
        flaresolverr_request = {
            "cmd": "request.{}".format(method.lower()),
            "url": url,
            "session": self.flaresolverr_session,
            "maxTimeout": 60000,
        }

        if cookies:
            flaresolverr_request["cookies"] = cookies

        flaresolverr_response = None
        last_error = None

        for try_count in range(tries):
            try:
                flaresolverr_response = self.session.post(
                    self.flaresolverr_url, json=flaresolverr_request
                )

                status_code = flaresolverr_response.status_code

                if status_code >= 500:
                    raise ValueError(
                        "FlareSolverr request failed, got status code {}: {}".format(status_code, flaresolverr_response.content)
                    )

                break
            except Exception as error:
                print(
                    "FlareSoverr error {}/{}".format(try_count, tries))
                last_error = error

        if not flaresolverr_response and last_error:
            raise last_error

        return flaresolverr_response