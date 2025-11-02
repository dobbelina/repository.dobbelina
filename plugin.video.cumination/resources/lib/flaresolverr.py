import requests
import time


class FlareSolverrManager:
    def __init__(self, flaresolverr_url=None, session_id=None):
        self.session = requests.session()
        self.flaresolverr_url = flaresolverr_url or "http://localhost:8191/v1"
        self.session_id = session_id or "cumination_session_{}".format(int(time.time()))

        # Only clear old cumination sessions to avoid conflicts with other addons
        self.clear_old_sessions()

        # Try to create session
        session_create_request = {"cmd": "sessions.create", "session": self.session_id}
        try:
            session_create_response = requests.post(
                self.flaresolverr_url,
                json=session_create_request,
                timeout=10
            )
            response_data = session_create_response.json()

            if response_data.get("status") == "error":
                # Session might already exist, use it
                self.flaresolverr_session = self.session_id
            else:
                self.flaresolverr_session = response_data.get("session", self.session_id)
        except Exception as e:
            raise RuntimeError(
                "Failed to connect to FlareSolverr at {}: {}. "
                "Please check if FlareSolverr is running and configured correctly in addon settings.".format(
                    self.flaresolverr_url, str(e)
                )
            )

    def __del__(self):
        session_destroy_request = {"cmd": "sessions.destroy", "session": self.flaresolverr_session}
        requests.post(self.flaresolverr_url, json=session_destroy_request)

    def clear_old_sessions(self):
        """Clear only old cumination sessions to avoid conflicts with other addons"""
        try:
            # Get session list
            session_list_request = {"cmd": "sessions.list"}
            session_list_response = requests.post(
                self.flaresolverr_url, json=session_list_request, timeout=5
            )

            sessions = session_list_response.json().get("sessions", [])

            # Clear only our old cumination sessions (identified by prefix)
            if sessions:
                for session_id in sessions:
                    if isinstance(session_id, str) and session_id.startswith("cumination_session_"):
                        # Don't clear the current session we're trying to use
                        if session_id != self.session_id:
                            session_destroy_request = {"cmd": "sessions.destroy", "session": session_id}
                            requests.post(self.flaresolverr_url, json=session_destroy_request, timeout=5)
        except Exception:
            # If clearing fails, continue anyway - not critical
            pass

    def request(self, url, method="GET", cookies=None, post_data=None, tries=3, max_timeout=60000):
        """
        Make a request through FlareSolverr to bypass Cloudflare protection.

        Args:
            url: The URL to request
            method: HTTP method (GET or POST)
            cookies: Optional cookies to send with request
            post_data: Optional POST data (for POST requests)
            tries: Number of retry attempts
            max_timeout: Maximum timeout in milliseconds (default 60s)

        Returns:
            Response object from FlareSolverr

        Raises:
            RuntimeError: If FlareSolverr request fails after all retries
        """
        flaresolverr_request = {
            "cmd": "request.{}".format(method.lower()),
            "url": url,
            "session": self.flaresolverr_session,
            "maxTimeout": max_timeout,
        }

        if cookies:
            flaresolverr_request["cookies"] = cookies

        if post_data and method.upper() == "POST":
            flaresolverr_request["postData"] = post_data

        flaresolverr_response = None
        last_error = None

        for try_count in range(1, tries + 1):
            try:
                # Give FlareSolverr extra time to solve challenge (timeout + 10s buffer)
                request_timeout = (max_timeout / 1000) + 10

                flaresolverr_response = self.session.post(
                    self.flaresolverr_url,
                    json=flaresolverr_request,
                    timeout=request_timeout
                )

                status_code = flaresolverr_response.status_code

                if status_code >= 500:
                    raise ValueError(
                        "FlareSolverr server error (HTTP {}): {}".format(
                            status_code,
                            flaresolverr_response.text[:200]
                        )
                    )

                # Check the FlareSolverr response status
                response_json = flaresolverr_response.json()
                if response_json.get("status") == "error":
                    error_msg = response_json.get("message", "Unknown error")
                    raise ValueError("FlareSolverr error: {}".format(error_msg))

                # Success!
                break

            except requests.exceptions.Timeout:
                last_error = RuntimeError(
                    "FlareSolverr timeout after {}s (try {}/{})".format(
                        request_timeout, try_count, tries
                    )
                )
                print(str(last_error))
            except requests.exceptions.ConnectionError as e:
                last_error = RuntimeError(
                    "Cannot connect to FlareSolverr at {} (try {}/{}): {}".format(
                        self.flaresolverr_url, try_count, tries, str(e)
                    )
                )
                print(str(last_error))
            except Exception as error:
                last_error = RuntimeError(
                    "FlareSolverr error (try {}/{}): {}".format(
                        try_count, tries, str(error)
                    )
                )
                print(str(last_error))

            # Wait a bit before retrying (exponential backoff)
            if try_count < tries:
                wait_time = try_count * 2
                print("Waiting {}s before retry...".format(wait_time))
                time.sleep(wait_time)

        if not flaresolverr_response and last_error:
            raise last_error

        return flaresolverr_response
