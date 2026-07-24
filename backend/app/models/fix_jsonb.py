import os, glob

files = glob.glob('*.py')
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if 'from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON' in content:
        content = content.replace('from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON', 'from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON\nfrom sqlalchemy import JSON')
        
        # safely replace JSONB references
        content = content.replace('JSON().with_variant(JSONB, 'postgresql'),', "JSON().with_variant(JSON().with_variant(JSONB, 'postgresql'), 'postgresql'),")
        content = content.replace('JSON().with_variant(JSONB, 'postgresql'))', "JSON().with_variant(JSON().with_variant(JSONB, 'postgresql'), 'postgresql'))")
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
