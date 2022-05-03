from mul.mulstart import MulStart
import logging

logging.basicConfig(level=logging.INFO, filename='log.txt', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == '__main__':

    t = MulStart()
    t.run()    