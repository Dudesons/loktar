from swagger_tester import swagger_test

# Dict containing the error you don't want to raise.
# By default, every status_code over other than 1xx, 2xx or 3xx
# will be considered as an error.
authorize_error = {
    'get': {
        '/artifact/{storage_backend}/{bucket_name}/{artifact_name}': [200]
    }
}

# Run the test with connexion
# An AssertionError will be raise in case of error.
swagger_test('/app/storage_proxy/swagger.yaml', authorize_error=authorize_error)
