import tool,json,re,urllib,sys
from urllib.parse import urlparse, parse_qs, unquote
def parse(data):
    info = data[:]
    server_info = urlparse(info)
    try:
        netloc = tool.b64Decode(server_info.netloc).decode('utf-8')
    except:
        netloc = server_info.netloc
    _netloc = netloc.split("@")
    _netloc_parts = _netloc[1].rsplit(":", 1)
    if _netloc_parts[1].isdigit(): #fuck
        server = re.sub(r"\[|\]", "", _netloc_parts[0])
        server_port = int(_netloc_parts[1])
    else:
        return None
    netquery = dict(
        (k, v if len(v) > 1 else v[0])
        for k, v in parse_qs(server_info.query).items()
    )
    if netquery.get('remarks'):
        remarks = netquery['remarks']
    else:
        remarks = server_info.fragment
    node = {
        'tag': unquote(remarks) or tool.genName()+'_vless',
        'type': 'vless',
        'server': server,
        'server_port': server_port,
        'uuid': _netloc[0].split(':', 1)[-1],
        'packet_encoding': netquery.get('packetEncoding', 'xudp')
    }
    if netquery.get('flow'):
        node['flow'] = 'xtls-rprx-vision'
    if netquery.get('security', '') not in ['None', 'none', ''] or netquery.get('tls') == '1':
        node['tls'] = {
            'enabled': True,
            'insecure': True,
            'server_name': ''
        }
        if netquery.get('allowInsecure') == '0':
            node['tls']['insecure'] = False
        node['tls']['server_name'] = netquery.get('sni', '') or netquery.get('peer', '')
        if node['tls']['server_name'] == 'None':
            node['tls']['server_name'] = ''
        if netquery.get('fp'):
            node['tls']['utls'] = {
                'enabled': True,
                'fingerprint': netquery['fp']
            }
        if netquery.get('security') == 'reality' or netquery.get('pbk'): #shadowrocket
            node['tls']['reality'] = {
                'enabled': True,
                'public_key': netquery.get('pbk'),
            }
            if netquery.get('sid'):
                node['tls']['reality']['short_id'] = netquery['sid']
            node['tls']['utls'] = {
                'enabled': True,
                'fingerprint': 'chrome'
            }
    if netquery.get('type'):
        if netquery['type'] == 'http':
            node['transport'] = {
                'type':'http'
            }
        elif netquery['type'] == 'ws':
            node['transport'] = {
                'type':'ws',
                "path": netquery.get('path', '').rsplit("?")[0],
                "headers": {
                    "Host": '' if netquery.get('host') is None and netquery.get('sni') == 'None' else netquery.get('host', netquery.get('sni', ''))
                }
            }
            if node.get('tls'):
                if node['tls']['server_name'] == '':
                    if node['transport']['headers']['Host']:
                        node['tls']['server_name'] = node['transport']['headers']['Host']
            if '?ed=' in netquery.get('path', ''):
                node['transport']['early_data_header_name'] = 'Sec-WebSocket-Protocol'
                node['transport']['max_early_data'] = int(re.search(r'\d+', netquery.get('path').rsplit("?ed=")[1]).group())
        elif netquery['type'] == 'grpc':
            node['transport'] = {
                'type':'grpc',
                'service_name':netquery.get('serviceName', '')
            }
    elif netquery.get('obfs'):  #shadowrocket
        if netquery['obfs'] == 'websocket':
            node['transport'] = {
                'type':'ws',
                "path": netquery.get('path', '').rsplit("?")[0],
                "headers": {
                    "Host": '' if netquery.get('obfsParam') is None and netquery.get('sni') == 'None' else netquery.get('obfsParam', netquery.get('sni', ''))
                }
            }
            if node.get('tls'):
                if node['tls']['server_name'] == '':
                    if node['transport']['headers']['Host']:
                        node['tls']['server_name'] = node['transport']['headers']['Host']
            if '?ed=' in netquery.get('path', ''):
                node['transport']['early_data_header_name'] = 'Sec-WebSocket-Protocol'
                node['transport']['max_early_data'] = int(re.search(r'\d+', netquery.get('path').rsplit("?ed=")[1]).group())
    if netquery.get('protocol'):
        node['multiplex'] = {
            'enabled': True,
            'protocol': netquery['protocol']
        }
        if netquery.get('max-streams'):
            node['multiplex']['max_streams'] = int(netquery['max-streams'])
        else:
            node['multiplex']['max_connections'] = int(netquery['max-connections'])
            node['multiplex']['min_streams'] = int(netquery['min-streams'])
        if netquery.get('padding') == 'True':
            node['multiplex']['padding'] = True
    return node