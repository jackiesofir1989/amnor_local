from . import lamp, transport, blower, alert_event, system_layout_config, sensor, spectrum_profile_config, \
    schedule_profile_config, mixer_table_config


def add_routes(app):
    app.include_router(lamp.router)
    app.include_router(alert_event.router)
    app.include_router(sensor.router)
    app.include_router(blower.router)
    app.include_router(transport.router)
    app.include_router(system_layout_config.router)
    # app.include_router(spectrum_profile.router)
    # app.include_router(schedule_profile.router)
    app.include_router(spectrum_profile_config.router)
    app.include_router(schedule_profile_config.router)
    app.include_router(mixer_table_config.router)
