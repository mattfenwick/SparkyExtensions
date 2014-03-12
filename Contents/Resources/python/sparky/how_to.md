adding a sparky extension:

 1. create module in <sparky_install_directory>/python/sparky/
 2. extend <sparky_install_directory>/python/sparky/sparky_site.py

   - menu syntax
   
        ('Reproduciblity!',         
          (
           ('re', 'Reproducibility',    ('reproduce', 'doit')),
           ('rr', 'Repro2',             ('reproduce', 'doittoit'))))
     
           a      b                       c           d
    
   - a: keyboard accelerator
   - b: name appearing in menu
   - c: module name -- goes in <sparky_install_directory>/python/sparky/...
   - d: function name in module

 3. call extension either by clicking in menu or using two-key shortcut
