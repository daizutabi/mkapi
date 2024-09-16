def test_get_config():
    from mkapi.config import MkApiConfig, get_config

    config = get_config()
    assert isinstance(config, MkApiConfig)


def test_set_config():
    from mkapi.config import MkApiConfig, get_config, set_config

    config: MkApiConfig = MkApiConfig()  # type: ignore
    set_config(config)  # type: ignore
    config_ = get_config()
    assert config is config_
