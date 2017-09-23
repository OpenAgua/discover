import json
from io import BytesIO

from mapbox import Uploader

from ..users import get_hydrausers
from ..studies import get_studies
from ..connection import connection
from ..network_editor.utils import correct_network_geojson, make_feature_collection


def decrypt(ciphertext, key):
    key = key
    f = Fernet(key)
    try:
        try:
            txt = f.decrypt(ciphertext).decode()
        except:
            txt = f.decrypt(bytes(ciphertext, 'utf-8')).decode()
    except:
        txt = None
    return txt


def correct_network_geojson(network, template):
    corrected_nodes = []
    try:
        for node in network.nodes:
            node['layout']['geojson'] = make_geojson_from_node(node, template)
            corrected_nodes.append(node)
        network['nodes'] = corrected_nodes
    except:
        pass

    corrected_links = []
    for link in network.links:
        link['layout']['geojson'] = make_geojson_from_link(network, link, template)
        corrected_links.append(link)
    network['links'] = corrected_links

    return network


def update_network_tiles(url, mapbox_username, mapbox_datasetname):
    hydrausers = get_hydrausers(url=url)

    geojson = {"type": "FeatureCollection", "features": []}
    for hydrauser in hydrausers:
        conn = connection(url=url, username=hydrauser.hydra_username, session_id=hydrauser.hydra_sessionid)
        studies = get_studies(hydrauser_id=hydrauser.id)
        for study in studies:
            networks = conn.call2('get_networks', project_id=study.project_id, summary=False)
            if 'faultstring' not in networks:
                for network in networks:
                    if 'public' in network.layout and network.layout.public:
                        template = conn.get_template_from_network(network)
                        network = correct_network_geojson(network, template)
                        try:
                            fc = make_feature_collection(network, template)
                            geojson['features'].extend(fc['features'])
                        except:
                            continue

    resp = upload_to_mapbox(mapbox_username, mapbox_datasetname, geojson)

    return resp


def upload_to_mapbox(username, datasetname, geojson):
    if type(geojson) == dict:
        geojson = json.dumps(geojson)
    if type(geojson) == str:
        geojson = BytesIO(geojson.encode())
    # see: https://www.mapbox.com/api-documentation/#uploads

    # Acquisition of credentials, staging of data, and upload
    # finalization is done by a single method in the Python SDK.
    service = Uploader()
    dataset_name = '{}.{}'.format(username, datasetname)
    resp = service.upload(geojson, dataset_name)

    return resp
