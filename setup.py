import sys
import subprocess

subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip', 'wheel'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])

if __name__ == '__main__':
    pass