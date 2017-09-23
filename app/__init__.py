from flask import Flask

app = Flask(__name__, instance_relative_config=True)

# CONFIGURATION

# default configuration (will move to object?)
app.config.from_object('config')
instance_cfg = 'instance_config.py'
if os.path.exists(os.path.join(app.instance_path, instance_cfg)):
    app.config.from_pyfile(instance_cfg)

