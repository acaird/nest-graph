#!/usr/bin/env python3
#
# formatted with black
#

import json
import requests
import sys
from os import getenv


def get_nest_access_token(
    client_id,
    client_secret,
    authorization_code,
    grant_type="authorization_code",
    url="https://api.home.nest.com/oauth2/access_token",
):

    print(
        "Client ID: {}\nClient Secret: {}\nAuthorization Code (PIN): {}".format(
            client_id, client_secret, authorization_code
        )
    )
    results = requests.post(
        url,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": grant_type,
            "code": authorization_code,
        },
    )

    if results.status_code != requests.codes.ok:
        print(
            """===> Error getting access code from Nest.
     Do you have the correct client_id, client_secret,
     and authorization code (pin)?  See the Nest Developer
     Guide at https://developers.nest.com/ for information
     on getting them; they are required.
""",
            file=sys.stderr,
        )
        print("(Status code: {})".format(results.status_code))
        print("(Error data: {})".format(json.dumps(results.json())))
        sys.exit(1)

    return results.json()


def get_nest_temperatures(access_token, url="https://developer-api.nest.com/"):

    authz = "Bearer {}".format(access_token)
    headers = {"content-type": "application/json", "authorization": authz}

    results = requests.get(url, headers=headers, allow_redirects=False)

    # Nest always redirects, but it is good to check, just in case
    if results.status_code == requests.codes.temporary_redirect:
        url = results.headers["Location"]
        results = requests.get(url, headers=headers, allow_redirects=False)

    if results.status_code == requests.codes.ok:
        return results.json()
    else:
        return {"status_code": results.status_code, "reason": results.reason}


def print_results_stdout(results):

    if "devices" not in results:
        print("The Nest API returned no devices for your account", file=sys.stderr)
        sys.exit(1)

    if "structures" not in results:
        print("The Nest API returned no structures for your account", file=sys.stderr)
        sys.exit(1)

    if "thermostats" not in results["devices"]:
        print(
            "There don't seem to be any thermostats associated with your Nest account",
            file=sys.stderr,
        )
        sys.exit(1)

    for structure in results["structures"]:
        print(
            "{}: {}  Smoke detectors: {}  Thermostats: {}".format(
                results["structures"][structure]["name"],
                results["structures"][structure]["away"],
                len(results["structures"][structure]["smoke_co_alarms"]),
                len(results["structures"][structure]["thermostats"]),
            )
        )
    for tstat in results["devices"]["thermostats"]:
        temp_scale = results["devices"]["thermostats"][tstat]["temperature_scale"]
        ambient_temp_key = "ambient_temperature_{}".format(temp_scale.lower())
        target_temp_key = "target_temperature_{}".format(temp_scale.lower())
        print(
            "{:>25}: Currently: {}{}  Set to: {}{}   {:>7}".format(
                results["devices"]["thermostats"][tstat]["name_long"],
                results["devices"]["thermostats"][tstat][ambient_temp_key],
                temp_scale,
                results["devices"]["thermostats"][tstat][target_temp_key],
                temp_scale,
                results["devices"]["thermostats"][tstat]["hvac_state"].capitalize(),
            )
        )


if __name__ == "__main__":

    # nest_access_token = get_nest_access_token(
    #     getenv("NEST_CLIENT_ID"),
    #     getenv("NEST_CLIENT_SECRET"),
    #     getenv("NEST_AUTHORIZATION_CODE"),
    # )

    nest_access_token = {}
    nest_access_token["access_token"] = getenv("NEST_ACCESS_TOKEN")
    if nest_access_token["access_token"] is None:
        print("Please set the NEST_ACCESS_TOKEN environment variable")
        sys.exit(1)
    results = get_nest_temperatures(nest_access_token["access_token"])
    if "status_code" in results:
        print(json.dumps(results, indent=4))
    else:
        print_results_stdout(results)
