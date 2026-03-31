{
    'name': 'Custom Stock Inventory Report Date',
    'version': '1.0.0',
    'summary': 'Use custom stock move report date in quantity history wizard',
    'depends': ['stock'],
    'data': [
        'wizard/stock_quantity_history.xml',
        'views/stock_move_views.xml',
    ],
    'installable': True,
    'application': False,
}
