from base64 import b64encode, b64decode

from ledger.immutable_store.store import F
from ledger.immutable_store.stores.hash_store import HashStore
from plenum.persistence.orientdb_store import OrientDbStore


class OrientDbHashStore(HashStore):
    """
    Uses OrientDB to store leaf hashes and node hashes
    """

    def __init__(self, store: OrientDbStore):
        self.store = store
        self.leafHashClass = "LeafHashStore"
        self.nodeHashClass = "NodeHashStore"
        self.store.createClasses(self.classesNeeded())
        self.lastSerialNo = 0

    def writeLeaf(self, leafHash):
        """append the leaf to the leaf hash store"""
        self.store.client.command(
            "insert into {} (serialNo, leafHash) values ('{}', '{}')".format(
                self.leafHashClass, self.lastSerialNo + 1, self._tob64(leafHash)))
        self.lastSerialNo += 1

    def writeNode(self, node):
        start, height, nodeHash = node
        serialNo = self.getNodePosition(start, height)
        self.store.client.command(
            "insert into {} (serialNo, nodeHash) values ('{}', '{}')".format(
                self.nodeHashClass, serialNo, self._tob64(nodeHash)))

    def _tob64(self, hash):
        return b64encode(hash).decode('utf_8')

    def _fromb64(self, hash):
        return b64decode(hash.encode('utf_8'))

    def readLeaf(self, serialNo):
        return self._readOne(serialNo, self.leafHashClass, F.leafHash.name)

    def readNode(self, serialNo):
        return self._readOne(serialNo, self.nodeHashClass, F.nodeHash.name)

    def _readOne(self, pos, hashClass, attrib):
        self._validatePos(pos)
        resultSet = self.store.client.command(
            "select * from {} where serialNo={} limit 1".format(
                hashClass, pos))
        return self._fromb64(resultSet[0].oRecordData[attrib])

    def readLeafs(self, start, end):
        return self._readMultiple(start, end, self.leafHashClass,
                                  F.leafHash.name)

    def readNodes(self, start, end):
        return self._readMultiple(start, end, self.nodeHashClass,
                                  F.nodeHash.name)

    def _readMultiple(self, start, end, hashClass, attrib):
        """
        Returns a list of hashes with serial numbers between start
         and end, both inclusive.
         """
        self._validatePos(start, end)
        resultSet = self.store.client.command(
            "select * from {} where serialNo between {} and {}".format(
                hashClass, start, end))
        return [self._fromb64(r.oRecordData[attrib]) for r in resultSet]

    @staticmethod
    def _validatePos(start, end=None):
        if end:
            assert start < end, "start index must be less than end index"
        if start < 1:
            raise IndexError(
                "serialNo starts from 1, index requested: {}".
                    format(start))

    def createLeafHashClass(self):
        self._createHashClass(self.leafHashClass, {
            F.serialNo.name: "integer",
            F.leafHash.name: "string"
        }, F.leafHash.name)

    def createNodeHashClass(self):
        self._createHashClass(self.nodeHashClass, {
            F.serialNo.name: "integer",
            F.nodeHash.name: "string"
        }, F.nodeHash.name)

    def _createHashClass(self, className, attributes, index):
        self.store.createClass(className)
        self.store.createClassProperties(className, attributes)
        self.store.createIndexOnClass(className, index, "unique")

    def classesNeeded(self):
        return [(self.leafHashClass, self.createLeafHashClass),
                (self.nodeHashClass, self.createNodeHashClass)]
