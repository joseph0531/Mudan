editable_params_list = [
    {
        'name': 'TARGET_FC_2G',
        'path': ['burst_processing', 'TARGET_FC_2G'],
        'type': 'list_float',
        'description': '2G Target Frequencies (list of frequencies in Hz)',
        'example': '[2.4145e9, 2.4295e9, 2.4445e9, 2.4595e9]'
    },
    {
        'name': 'TARGET_FC_5G',
        'path': ['burst_processing', 'TARGET_FC_5G'],
        'type': 'list_float',
        'description': '5G Target Frequencies (list of frequencies in Hz)',
        'example': '[5.7965e9]'
    },
    {
        'name': 'NUM_WORKERS',
        'path': ['burst_processing', 'NUM_WORKERS'],
        'type': 'int',
        'description': 'Number of Workers',
        'example': '2'
    },
    {
        'name': 'PROCESS_WORKER_MULTIPLIER',
        'path': ['burst_processing', 'PROCESS_WORKER_MULTIPLIER'],
        'type': 'int',
        'description': 'Process Worker Multiplier',
        'example': '8'
    },
    {
        'name': 'BURST_WORKER_MULTIPLIER',
        'path': ['burst_processing', 'BURST_WORKER_MULTIPLIER'],
        'type': 'int',
        'description': 'Burst Worker Multiplier',
        'example': '3'
    },
    {
        'name': 'DO_SHIFT_IQ_FOR_SHM',
        'path': ['burst_processing', 'DO_SHIFT_IQ_FOR_SHM'],
        'type': 'bool',
        'description': 'Do Shift IQ for SHM',
        'example': 'false'
    },
    {
        'name': 'SKIP_ANT_LARGER_THAN',
        'path': ['burst_processing', 'SKIP_ANT_LARGER_THAN'],
        'type': 'int',
        'description': 'Skip Antenna Larger Than',
        'example': '0'
    },
    {
        'name': 'USE_LTE_RATE',
        'path': ['devices', 'sa', 'USE_LTE_RATE'],
        'type': 'bool',
        'description': 'Use LTE Rate',
        'example': 'true'
    },
    {
        'name': 'DURATION',
        'path': ['devices', 'sa', 'DURATION'],
        'type': 'float',
        'description': 'Duration (seconds)',
        'example': '0.35'
    },
    {
        'name': 'DECIMATION',
        'path': ['devices', 'sa', 'DECIMATION'],
        'type': 'int',
        'description': 'Decimation Factor',
        'example': '8'
    },
    {
        'name': 'BANDWIDTH',
        'path': ['devices', 'sa', 'BANDWIDTH'],
        'type': 'float',
        'description': 'Bandwidth (Hz)',
        'example': '60000000.0'
    },
    {
        'name': 'REF_LEVEL',
        'path': ['devices', 'sa', 'REF_LEVEL'],
        'type': 'int',
        'description': 'Reference Level (dBm)',
        'example': '10'
    },
    {
        'name': 'CORRECTION_CAPTURE',
        'path': ['devices', 'sa', 'CORRECTION_CAPTURE'],
        'type': 'bool',
        'description': 'Correction Capture',
        'example': 'false'
    },
    {
        'name': 'listener_broker',
        'path': ['mqtt', 'broker'],
        'type': 'str',
        'description': 'Listener Broker',
        'example': '140.112.45.232'
    },
    {
        'name': 'uploader_broker',
        'path': ['mqtt', 'uploader', 'broker'],
        'type': 'str',
        'description': 'Uploader Broker',
        'example': '140.112.45.232'
    }
]