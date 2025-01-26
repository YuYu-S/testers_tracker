import subprocess
import shutil
import sys
import os

# Function to build the app using PyInstaller
def build_app():
    print("Building the app using PyInstaller...")
    
    main = os.path.join("app", "main.py")
    
    # Define the image files to include (e.g., images, folders)
    image_folder = r"./images"

    # Define icon location
    icon = os.path.join("images", "seagate.ico")

    # Define exe file location
    build_dir = os.path.dirname(os.path.abspath(__file__))
    exe_dir   = os.path.join(build_dir, "output")
    
    # Installer location
    installer_loc = r"C:\Python38\Scripts\pyinstaller.exe"

    # Build the app with PyInstaller
    try:
        subprocess.check_call([
            installer_loc,
            '--onefile',
            '--noconsole',
            "--add-data", "app/data.py;app",
            "--add-data", "app/util.py;app",
            "--add-data", f'{image_folder};images',
            f"--icon={icon}",
            f"--distpath={exe_dir}",
            f"--name=Testers_Tracker",
            main
        ])
        print("App built successfully with PyInstaller.")

    except subprocess.CalledProcessError as e:
        print(f"Error building app: {e}")
        sys.exit(1)

# Function to clean up the build files
def clean_up():
    print("Cleaning up the build files...")
    
    # Remove PyInstaller's build and dist folders
    shutil.rmtree('build', ignore_errors=True)
    shutil.rmtree('dist', ignore_errors=True)
    shutil.rmtree('main.spec', ignore_errors=True)
    
    print("Clean up complete.")


# Main build function
def main():
    build_app()
    clean_up()


if __name__ == "__main__":
    main()
