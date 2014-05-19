

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
    ['HE21', 'NE2'  ],
    ['HE22', 'NE2'  ],
    ['HE1' , 'NE1'  ]
]

# how should ambiguity and sidechains be handled?
# e.g. 45[?]{C12}(1)    <-- is_sidechain in parens in group name?
#      7[HD2(1)]-8[ND2]-9[CB]    <-- ambiguity in parens in atomname?
#      4[H]-5[N]-6[CA(i-1)]
hncacb = [
    ['H'    , 'N'  , 'CA'       ],
    ['H'    , 'N'  , 'CA(i-1)'  ],
    ['H'    , 'N'  , 'CB'       ],
    ['H'    , 'N'  , 'CB(i-1)'  ],
    ['HE'   , 'NE' , 'CD'       ],
    ['HD21' , 'ND2', 'CB'       ],
    ['HD21' , 'ND2', 'CA'       ],
    ['HD22' , 'ND2', 'CB'       ],
    ['HD22' , 'ND2', 'CA'       ],
    ['HE21' , 'NE2', 'CG'       ],
    ['HE21' , 'NE2', 'CB'       ],
    ['HE22' , 'NE2', 'CG'       ],
    ['HE22' , 'NE2', 'CB'       ]
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
