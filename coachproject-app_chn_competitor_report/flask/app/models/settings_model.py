from .db import db


class AppSetting(db.Model):
    __tablename__ = "app_setting"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<AppSetting {self.name} = {self.value}>"

    def get_value(self):
        """Convert the value to the appropriate type based on the setting's type."""
        if self.type == "boolean":
            return self.value.lower() == "true"
        elif self.type == "integer":
            return int(self.value)
        # Add more types as needed (e.g., float, date, etc.)
        return self.value

    @staticmethod
    def is_last_year_data_editable():
        setting = AppSetting.query.filter_by(name="is_last_year_data_editable").first()
        is_editable = True
        if setting:
            is_editable = setting.get_value()

        return is_editable

    @staticmethod
    def toggle_last_year_data_editable():
        setting = AppSetting.query.filter_by(name="is_last_year_data_editable").first()
        if setting:
            # Toggle the value
            new_value = "false" if setting.value.lower() == "true" else "true"
            setting.value = new_value
            db.session.commit()

            return new_value


def initialize_settings():
    # Check if the table is empty
    if AppSetting.query.count() == 0:
        # Insert default settings if the table is empty
        default_settings = [
            AppSetting(name="is_last_year_data_editable", value="true", type="boolean"),
        ]

        # Add all default settings to the session
        db.session.bulk_save_objects(default_settings)
        db.session.commit()
        print("Default settings initialized.")
