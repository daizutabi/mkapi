def test_get_config():
    from mkapi.config import MkapiConfig, get_config

    config = get_config()
    assert isinstance(config, MkapiConfig)


def test_set_config():
    from mkapi.config import MkapiConfig, get_config, set_config

    config: MkapiConfig = MkapiConfig()  # type: ignore
    set_config(config)  # type: ignore
    config_ = get_config()
    assert config is config_
