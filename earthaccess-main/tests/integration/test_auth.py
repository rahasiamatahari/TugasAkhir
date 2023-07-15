# package imports
import logging
import os
import pathlib
import unittest

import earthaccess
import pytest

logger = logging.getLogger(__name__)
assertions = unittest.TestCase("__init__")

NETRC_PATH = pathlib.Path.home() / pathlib.Path(".netrc")


def activate_environment():
    earthaccess.__auth__ = earthaccess.Auth()
    # the original comes from github secrets
    os.environ["EARTHDATA_USERNAME"] = os.getenv("EARTHACCESS_TEST_USERNAME", "")
    os.environ["EARTHDATA_PASSWORD"] = os.getenv("EARTHACCESS_TEST_PASSWORD", "")


def activate_netrc():
    activate_environment()
    username = os.environ["EARTHDATA_USERNAME"]
    password = os.environ["EARTHDATA_PASSWORD"]

    with open(NETRC_PATH, "w") as f:
        f.write(
            f"machine urs.earthdata.nasa.gov login {username} password {password}\n"
        )
        os.chmod(NETRC_PATH, 0o600)


def delete_netrc():
    if NETRC_PATH.exists():
        NETRC_PATH.unlink()


def test_auth_can_read_earthdata_env_variables():
    activate_environment()
    auth = earthaccess.login(strategy="environment")
    logger.info(f"Current username: {auth.username}")
    logger.info(f"earthaccess version: {earthaccess.__version__}")

    assertions.assertIsInstance(auth, earthaccess.Auth)
    assertions.assertIsInstance(earthaccess.__auth__, earthaccess.Auth)
    assertions.assertTrue(earthaccess.__auth__.authenticated)


def test_auth_can_read_from_netrc_file():
    activate_netrc()
    auth = earthaccess.login(strategy="netrc")
    assertions.assertTrue(auth.authenticated)
    delete_netrc()


def test_auth_throws_exception_if_netrc_is_not_present():
    activate_environment()
    delete_netrc()
    with pytest.raises(Exception) as e_info:
        earthaccess.login(strategy="netrc")
        assertions.assertRaises(FileNotFoundError)
        print(e_info)


def test_auth_populates_attrs():
    activate_environment()
    auth = earthaccess.login(strategy="environment")
    assertions.assertIsInstance(auth, earthaccess.Auth)
    assertions.assertIsInstance(earthaccess.__auth__, earthaccess.Auth)
    assertions.assertTrue(earthaccess.__auth__.authenticated)


def test_auth_can_create_authenticated_requests_sessions():
    activate_environment()
    session = earthaccess.get_requests_https_session()
    assertions.assertTrue("Authorization" in session.headers)
    assertions.assertTrue("Bearer" in session.headers["Authorization"])


def test_auth_can_fetch_s3_credentials():
    activate_environment()
    auth = earthaccess.login(strategy="environment")
    assertions.assertTrue(auth.authenticated)
    for daac in earthaccess.daac.DAACS:
        if len(daac["s3-credentials"]) > 0:
            try:
                print(f"Testing S3 credentials for {daac['short-name']}")
                credentials = earthaccess.get_s3_credentials(daac["short-name"])
                assertions.assertIsInstance(credentials, dict)
                assertions.assertTrue("accessKeyId" in credentials)
            except Exception as e:
                print(
                    f"An error occured while trying to fetch S3 credentials for {daac['short-name']}: {e}"
                )
