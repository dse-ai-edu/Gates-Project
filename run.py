import argparse
from app import app

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='main')
    parser.add_argument('--port', type=int, default=8200)
    parser.add_argument('--mode', type=str, default='dev')
    args = parser.parse_args()
    
    app.config['mode'] = args.mode
    app.run(port=args.port, host="0.0.0.0", debug=True)