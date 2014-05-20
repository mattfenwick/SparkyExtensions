

orders = [
    [[0]],
    [[0, 1], [1,0]],
    [[0,1,2], [0,2,1], [1,0,2], [1,2,0], [2,0,1], [2,1,0]]
]

nhsqc = [
    ['H'   , 'N'    ],
    ['HE'  , 'NE'   ],
    ['HD21', 'ND2'  ],
    ['HD22', 'ND2'  ],
    ['HD2[12]', 'ND2']
    ['HE21', 'NE2'  ],
    ['HE22', 'NE2'  ],
    ['HE2[12]', 'NE2']
    ['H[DE][12]', 'N[DE]2']
    ['HE1' , 'NE1'  ]
]

hncacb = [
    ['H'    , 'N'  , 'CA'       ],
    ['H'    , 'N'  , 'CA(i-1)'  ],
    ['H'    , 'N'  , 'CA(i/i-1)'],
    ['H'    , 'N'  , 'CB'       ],
    ['H'    , 'N'  , 'CB(i-1)'  ],
    ['H'    , 'N'  , 'CB(i/i-1)'],
    ['HE'   , 'NE' , 'CD'       ],
    ['HD21' , 'ND2', 'CB'       ],
    ['HD22' , 'ND2', 'CB'       ],
    ['HD21' , 'ND2', 'CA'       ],
    ['HD22' , 'ND2', 'CA'       ],
    ['HD2[12]', 'ND2', 'CB'     ],
    ['HD2[12]', 'ND2', 'CA'     ],
    ['HE21' , 'NE2', 'CG'       ],
    ['HE22' , 'NE2', 'CG'       ],
    ['HE21' , 'NE2', 'CB'       ],
    ['HE22' , 'NE2', 'CB'       ],
    ['HE[12]', 'NE2', 'CG'      ],
    ['HE[12]', 'NE2', 'CB'      ],
    ['H[DE][12]', 'N[DE]2', 'CG'],
    ['H[DE][12]', 'N[DE]2', 'CB']
]

hn_co_cacb = [
    # what about sidechains?  is this complete?
    ['H'    , 'N'  , 'CA(i-1)'  ],
    ['H'    , 'N'  , 'CB(i-1)'  ]
]


spectra = {
    'NHSQC'     : nhsqc     ,
    'HNCACB'    : hncacb    ,
    'HN(CO)CACB': hn_co_cacb
}
