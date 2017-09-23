import os

from flask import render_template, request, json, jsonify, current_app

from .utils import *

@app.route('/')
# @login_required
def main():
    return render_template('discover.html')


@app.route('/upload_all', methods=['POST'])
def upload_all():
    mapbox_creation_token = request.form.get('mapbox_creation_token')
    os.environ['MAPBOX_ACCESS_TOKEN'] = mapbox_creation_token
    resp = update_network_tiles(
        url=current_app.config['HYDRA_URL'],
        mapbox_username=current_app.config['MAPBOX_USERNAME'],
        mapbox_datasetname=current_app.config['MAPBOX_DISCOVERY_TILESET_NAME']
    )

    resp = json.loads(resp.content.decode())

    return jsonify(resp=resp)

@app.route('/project/<study_id>')
# @login_required
def discover_study(study_id):
    study_id = int(study_id)
    study = get_study(id=study_id)
    invalid = True
    if study:
        hydrauser = get_hydrauser(id=study.hydrauser_id)
        conn = connection(
            url=current_app.config['HYDRA_URL'],
            username=hydrauser.hydra_username,
            password=decrypt(hydrauser.hydra_password),
        )
        project = conn.get_project(project_id=study.project_id)
        if 'faultstring' not in project:
            invalid = False
    if invalid:
        return '', 404
    else:
        return render_template('study.html', study=study_id)

@app.route('/get_study_geojson')
def get_study_geojson():

    study_id = request.args.get('id', type=int)
    study = get_study(id=study_id)

    hydrauser = get_hydrauser(id=study.hydrauser_id)
    conn = connection(
        url=current_app.config['HYDRA_URL'],
        username=hydrauser.hydra_username,
        password=decrypt(hydrauser.hydra_password),
    )

    networks = conn.call('get_networks', {
        'project_id': study.project_id,
        'include_data': 'N'
    })
    if 'faultstring' in networks:
        return '', 404

    features = []

    for network in networks:
        if 'public' in network.layout and network.layout.public:
            if 'active_template' in network.layout:
                template_name = network.layout.active_template
            else:
                template_name = network.types[0].template_name
            template = conn.call('get_template_by_name', {'template_name': template_name})
            fc = make_feature_collection(network, template)
            features.append(fc)

    return jsonify(features=features)


@app.route('/get_networks_geojson')
def get_networks_geojson():
    hydrausers = get_hydrausers(url=current_app.config['HYDRA_URL'])

    features = []

    for hydrauser in hydrausers:

        conn = connection(
            url=current_app.config['HYDRA_URL'],
            username=hydrauser.hydra_username,
            password=decrypt(hydrauser.hydra_password),
        )

        studies = get_studies(hydrauser_id=hydrauser.id)

        for study in studies:
            networks = conn.call('get_networks', {
                'project_id': study.project_id,
                'include_data': None
            })
            if 'faultstring' in networks:
                continue

            for network in networks:
                if 'public' in network.layout and network.layout.public:
                    # bb = conn.call('get_network_extents', {'network_id': network.id})
                    # lon = (float(bb.min_x) + float(bb.max_x)) / 2
                    # lat = (float(bb.min_y) + float(bb.max_y)) / 2
                    # if lon==0 and lat==0:
                    #     continue
                    # point = {
                    #     "type": "Point",
                    #     "coordinates": [lon, lat]
                    # }
                    # features.append(point)
                    template = conn.get_template(template_id=network.types[0].template_id)
                    fc = make_feature_collection(network, template)
                    features.append(fc)

    return jsonify(features=features)
