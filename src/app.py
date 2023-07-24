import threading

from src.api.server import start_server
from src.services.consumer import Consumer


def main():
    '''
    Main function responsible for running the consumer until prefetching is complete
    then starts the API server
    '''
    prefetch_complete = threading.Event()
    consumer = Consumer(prefetch_complete, debug=True)
    consumer_thread = threading.Thread(
        target=consumer.start,
        daemon=True,  # Auto-terminates when main() is interrupted
    )
    consumer_thread.start()

    # Waits until the consumer has finished prefetching before starting the API server
    prefetch_complete.wait()
    start_server(debug=False)


if __name__ == "__main__":
    main()
