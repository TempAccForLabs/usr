from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    # added for jwt 
    JWT_SECRET:str
    JWT_ALGORITHM:str
    # easy to forget, takes an extra day of debugging to find missing
    # added for totp encryption
    TOTP_ENCRYPTION_KEY: str

    # the model_config attr of the Settings child class allows for the
    # modification of the configuration of any PYDANTIC class
    # the SettingsConfigDict reads from the .env file
    model_config = SettingsConfigDict(
        env_file = ".env",
        # ignore extra attributes within the settings class
        extra="ignore"
    )

# so that we do not instantiate every time we need .env variable access
Config = Settings()    

