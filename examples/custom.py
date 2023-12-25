def on_config():
    # Here you can do all you want.
    print("Called.")


def on_config_with_config(config):
    print("Called with config.")
    print(config["docs_dir"])

    # You can change config, for example:
    # config['docs_dir'] = 'other_directory'

    # Optionally, you can return altered config to customize MkDocs.
    # return config


def on_config_with_mkapi(config, mkapi):
    print("Called with config and mkapi.")
    print(config["docs_dir"])
    print(mkapi)
