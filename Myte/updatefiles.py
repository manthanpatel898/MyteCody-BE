import os
import shutil

# Define source and destination directories
src_be = r'C:\Users\ahmed\GitHub\MyteCody-BE'
src_fe = r'C:\Users\ahmed\GitHub\MyteCody-FE'
dest_base = r'C:\Users\ahmed\GitHub\MyteCodyQualityCheck'

# Define the destination subdirectories
dest_be = os.path.join(dest_base, 'MyteCody-BE')
dest_fe = os.path.join(dest_base, 'MyteCody-FE')


def copy_directory(src, dest):
    # If destination directory exists, remove it first to ensure a clean copy
    if os.path.exists(dest):
        shutil.rmtree(dest)

    # Copy source directory to destination
    shutil.copytree(src, dest)
    print(f"Copied {src} to {dest}")


# Copy BE and FE directories
copy_directory(src_be, dest_be)
copy_directory(src_fe, dest_fe)

print("All directories copied successfully!")
