def test_get_config():
    from mkapi.config import Config, get_config

    config = get_config()
    assert isinstance(config, Config)


def test_set_config():
    from mkapi.config import Config, get_config, set_config

    config: Config = Config()  # type: ignore
    set_config(config)  # type: ignore
    config_ = get_config()
    assert config is config_
