import multiprocessing
from alg.grubcut import grubcut

class GrabCut(multiprocessing.Process):

    def __init__(self, conn, img_path, pts = [], feats = []):
        super(GrabCut, self).__init__()
        self.conn = conn
        self.pts = pts
        self.feats = feats
        self.img_path = img_path
    def run(self):
        result = []
        for i, p in enumerate(self.pts):
            r = grubcut(self.img_path, p, False, True, False)
            result.append([r, self.feats[i]])
            self.conn.send(i)
        self.conn.send(result)

