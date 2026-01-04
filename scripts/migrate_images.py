import os
import shutil

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
old_dir = os.path.join(base_dir, 'static', 'uploads', 'products')
new_dir = os.path.join(base_dir, 'static', 'img', 'products')
fe_dir = os.path.abspath(os.path.join(base_dir, '..', 'Web-ecommerce-kopi FE', 'img', 'products'))
print('Old dir:', old_dir)
print('New dir:', new_dir)
print('FE dir:', fe_dir)
moved = 0
if not os.path.exists(old_dir):
    print('No old uploads directory found, nothing to do.')
else:
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    if not os.path.exists(fe_dir):
        os.makedirs(fe_dir)
    for fname in os.listdir(old_dir):
        if not fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            continue
        src = os.path.join(old_dir, fname)
        dst_new = os.path.join(new_dir, fname)
        dst_fe = os.path.join(fe_dir, fname)
        try:
            shutil.copy2(src, dst_new)
            shutil.copy2(src, dst_fe)
            moved += 1
        except Exception as e:
            print('Failed copy', fname, e)
    print(f'Copied {moved} files to new static img and FE img folder.')