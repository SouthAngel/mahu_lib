#coding=utf-8
# 2025 02 17
# Author:PengCheng
import sys,os
import re
import json
import time
import threading
import sqlite3
import PySide2.QtWidgets as qw
import PySide2.QtCore as qc
import PySide2.QtGui as qg


MHLIB_VERSION = '1.0.1 PY3.10 2025 02 21'
GDT = {}


# #### core


class CoreUtilities(object):
    def __init__(self):
        super().__init__()
    
    @staticmethod
    def sqlReadOnlyConnect(_i):
        return 'file:%s?mode=ro'%(_i.replace('\\','/'))

    @staticmethod
    def convertLowImage(source_img, output_img, width=128, height=128):
        img_so = qg.QImage()
        img_so.load(source_img)
        img_sc = img_so.scaled(width,height)
        img_out = qg.QImage(width, height, qg.QImage.Format_RGB32)
        for x in range(width):
            for y in range(height):
                img_out.setPixel(x,y,img_sc.pixel(x,y))
        img_out.save(output_img, 'JPG', 92)


    @staticmethod
    def hashstr(_i):
        return hex(hash(_i)).replace('0x','').replace('-','_')

class Importer(object):
    def __init__(self):
        super().__init__()
        self.app = self.__getApp()
    
    def __getApp(self):
        ret = ''
        def thou():
            import hou
            if hou.node('/'):
                return 'HOUDINI'
        def tmaya():
            import maya.cmds
            maya.cmds.about(q=1,a=1)
            return 'MAYA'
        for ef in (thou,tmaya):
            try:
                ret = ef()
            except Exception as e:
                pass
            if ret:
                break
        return ret or ''

    def import_maya(self, path):
        import maya.cmds as cmds
        def maya_ma():
            cmds.file(path,i=1)
        def maya_usd():
            cmds.file(path,i=1,type="USD Import")
        ext_dec = (
            (maya_ma, '*.ma,*.mb,*.abc,*.obj'),
            (maya_usd, '*.usd,*.usdc,*.usda'),
            )
        for fn,fextd in ext_dec:
            for fext in fextd.split(','):
                rec = re.compile(fext.strip(' ,.').replace('.','\\.').replace('*','.*')+'$', re.I)
                if rec.match(path):
                    fn()
                    return

    def import_houdini(self, path):
        print(['def import_houdini(self, path):', path])
        import hou
        fname = os.path.basename(path)
        fxext = os.path.splitext(fname)
        def createNodePath(_path):
            psp = _path.split('/')
            nsp = []
            tsp = []
            cnode = None
            for each in psp:
                fi = each.find('[')
                if fi > -1:
                    nsp.append(each[:fi])
                    tsp.append(each[(fi+1):-1])
                else:
                    nsp.append(each)
                    tsp.append('')
            nsp = list(map(lambda x:x.replace(' ','_').replace('-','_'), nsp))
            for i in range(1,len(psp)):
                pathstp = nsp[:i]
                pathstc = nsp[:(i+1)]
                cnode = hou.node('/'.join(pathstc))
                if not cnode:
                    cnode = hou.node('/'.join(pathstp)).createNode(tsp[i],nsp[i])
            return cnode

        def houdini_hip():
            hou.hipFile.merge(path)
        def houdini_geo():
            fnode = createNodePath('/obj/%s[geo]/%s[file]'%(fxext[0],fxext[0]))
            fnode.parm('file').set(path)
            fnode.setCurrent(True)
            fnode.setDisplayFlag(True)
        def houdini_abc():
            fnode = createNodePath('/obj/%s[geo]/%s[alembic]'%(fxext[0],fxext[0]))
            fnode.parm('fileName').set(path)
            fnode.setCurrent(True)
            fnode.setDisplayFlag(True)
        def houdini_jpg():
            fnode = createNodePath('/img[img]/comp1[img]/%s[file]'%(fxext[0]))
            fnode.parm('filename1').set(path)
            fnode.setCurrent(True)
            fnode.setDisplayFlag(True)
        def houdini_usd():
            fnode = createNodePath('/stage/%s[reference]'%(fxext[0]))
            fnode.parm('filepath1').set(path)
            fnode.setCurrent(True)
            fnode.setDisplayFlag(True)

        ext_dec = (
            (houdini_abc,'*.abc',),
            (houdini_hip,'*.hip,*.hiplc,*.hipnc',),
            (houdini_usd,'*.usd, *.usda, *.usdc, *.usdz, *.mtlx',),
            (houdini_geo,'*.geo, *.bgeo, *.hclassic, *.bhclassic, *.geo.gz, *.geogz, *.bgeo.gz, '\
            '*.bgeogz, *.hclassic.gz, *.hclassicgz, *.bhclassic.gz, *.bhclassicgz, *.geo.sc, *.geosc, '\
            '*.bgeo.sc, *.bgeosc, *.hclassic.sc, *.hclassicsc, *.bhclassic.sc, *.bhclassicsc, *.json, '\
            '*.bjson, *.json.gz, *.jsongz, *.bjson.gz, *.bjsongz, *.json.sc, *.jsonsc, *.bjson.sc, *.bjsonsc, '\
            '*.poly, *.bpoly, *.d, *.rib, *.flt, *.hgt, *.r16, *.r32, *.img, *.tif, *.tiff, *.png, *.jpg, '\
            '*.exr, *.pic, *.obj, *.GoZ, *.vdb, *.usd, *.usda, *.usdc, *.bhclassic.lzma, *.bgeo.lzma, '\
            '*.hclassic.bz2, *.bgeo.bz2, *.pc, *.pmap, *.geo.lzma, *.ply, *.pdb, *.off, *.iges, *.igs, '\
            '*.hclassic.lzma, *.lw, *.lwo, *.geo.bz2, *.bstl, *.eps, *.ai, *.stl, *.dxf, *.bhclassic.bz2, *.abc, *.fbx',),
            (houdini_jpg,'*.pic, *.pic.Z, *.picZ, *.pic.gz, *.picgz, *.rat, *.tbf, *.dsm, *.picnc, '\
            '*.piclc, *.rgb, *.rgba, *.sgi, *.tif, *.tif3, *.tif16, *.tif32, *.tiff, *.tx, *.yuv, *.pix, '\
            '*.als, *.cin, *.kdk, *.jpg, *.jpeg, *.exr, *.png, *.psd, *.psb, *.si, *.tga, *.vst, *.vtg, '\
            '*.rla, *.rla16, *.rlb, *.rlb16, *.bmp, *.hdr, *.ptx, *.ptex, *.ies, *.dds, *.r16, *.r32, *.qtl',),
        )
        for fn,fextd in ext_dec:
            for fext in fextd.split(','):
                rec = re.compile(fext.strip(' ,.').replace('.','\\.').replace('*','.*')+'$', re.I)
                if rec.match(path):
                    fn()
                    return

class Lock4Write(object):
    def __init__(self, _path):
        super().__init__()
        self.file_path = _path
        self.haslock = False
    
    def lock(self):
        try:
            open(self.file_path, 'wb').write(b'b1')
            self.haslock = True
        except Exception as e:
            print([e])

    def unlock(self):
        if self.haslock and os.path.isfile(self.file_path):
            try:
                os.remove(self.file_path)
                self.haslock = False
            except Exception as e:
                print([e])
    
    def __del__(self):
        self.unlock()

class CoreProject(object):
    def __init__(self):
        super().__init__()
        self.root_dir = ''
        self.thumbs_dir = ''
        self.project_db = ''
        self.asset_db = ''
        self.index_db = ''
        self.lock_f = ''
        self.u_f = ''
        self.can_write = -1
    
    def setRootPath(self, _path):
        self.root_dir = _path
        self.thumbs_dir = os.path.join(_path, 'thumbs')
        self.project_db = os.path.join(_path, 'project.db')
        self.asset_db = os.path.join(_path, 'asset.db')
        self.index_db = os.path.join(_path, 'index.db')
        self.lock_f = os.path.join(_path, '_lock.db')
        self.u_f = os.path.join(_path, 'u_lock.db')

    def exists(self):
        for d in (self.root_dir,self.thumbs_dir):
            if not os.path.isdir(d):
                return False
        for f in (self.project_db,self.asset_db,self.index_db):
            if not os.path.isfile(f):
                return False
        return True

    def create(self):
        if not os.path.isdir(self.root_dir):
            os.makedirs(self.root_dir)
        os.mkdir(self.thumbs_dir)
        import socket
        open(self.u_f,'w').write(socket.gethostname())
        conn = sqlite3.connect(self.project_db)
        cur = conn.cursor()
        cur.execute('CREATE TABLE project (k TEXT PRIMARY KEY  NOT NULL, v TEXT)')
        data = [('creator',socket.gethostname()),('create_time',str(time.time())),('description',''),('name',os.path.basename(self.root_dir))]
        cur.executemany('INSERT INTO project VALUES (?,?)',data)
        conn.commit()
        conn.close()
        conn = sqlite3.connect(self.asset_db)
        cur = conn.cursor()
        cur.execute('CREATE TABLE asset_db (id INTERGER PRIMARY KEY  NOT NULL, name TEXT, path TEXT, gid INTERGER, description TEXT, thumbh TEXT, thumbl TEXT)')
        cur.execute('CREATE INDEX gid_index ON asset_db (gid)')
        cur.execute('CREATE TABLE group_db (id INTERGER PRIMARY KEY  NOT NULL, name TEXT, pid INTERGER, description TEXT)')
        cur.execute('INSERT INTO group_db (id,pid,name) VALUES (?,?,?)',(1,0,os.path.basename(self.root_dir)))
        conn.commit()
        conn.close()
        conn = sqlite3.connect(self.index_db)
        cur = conn.cursor()
        cur.execute('CREATE TABLE tags(id  INTERGER  PRIMARY KEY  NOT NULL, tag  TEXT  NOT NULL)')
        cur.execute('CREATE INDEX tag_name_index ON tags (tag)')
        cur.execute('CREATE TABLE taglink (asset_id INTERGER  NOT NULL, tag_id INTERGER  NOT NULL)')
        cur.execute('CREATE INDEX tag_asset_index ON taglink (asset_id,tag_id)')
        conn.commit()
        conn.close()
    
    def canIWrite(self):
        if self.can_write != -1:
            return self.can_write
        ret = False
        import socket
        try:
            open(self.u_f,'w').write(socket.gethostname())
            ret = True
        except Exception as e:
            print([e])
        self.can_write = ret
        return ret

    def getLock(self):
        return Lock4Write(self.lock_f)

class LocalData(object):
    def __init__(self):
        super().__init__()
        self.fdpath = os.path.join(os.getenv('TEMP'), 'mahu_library_03d2d278')
        self.d = {}
        self.load()
    
    def load(self):
        try:
            with open(self.fdpath) as _f:
                self.d = json.load(_f)
        except Exception as e:
            print([e])
    
    def dump(self):
        try:
            with open(self.fdpath, 'w') as _f:
                json.dump(self.d, _f)
        except Exception as e:
            print([e])
    
    def __getitem__(self,k):
        return self.d.get(k, '')

    def __setitem__(self,k,v):
        self.d[k] = v
        self.dump()
        self.load()

# #### ui


class BackgroundT(qc.QThread):
    class BO(qc.QObject):
        invoke = qc.Signal()
        def __init__(self):
            super().__init__()
            self.invf = self.testEcho
            self.is_busy = 0
            self.invoke.connect(self.invfc)
        
        def testEcho(self):
            print('test echo run in %s'%(self.thread()))
        
        def invfc(self):
            self.is_busy = 1
            self.invf()
            self.is_busy = 0

    loadedOneItem = qc.Signal(int)
    def __init__(self, data):
        super().__init__()
        self.d = data
        self.bg = self.BO()
        self.bg.moveToThread(self)
        self.start()
    
    def run(self):
        print('background start')
        self.exec_()
        print('background end')
    
    def invoke(self, fn):
        self.bg.invf = fn
        self.bg.invoke.emit()

    def isBusy(self):
        return self.bg.is_busy

class TIListModel(qg.QStandardItemModel):
    def __init__(self, parent):
        super().__init__(parent)
        for i in range(12):
            for j in range(14):
                self.setItem(i,j,qg.QStandardItem("item_%d_%d"%(i,j)))
    
    def data(self, index, role=None):
        # tret = super().data(index, role)
        tret = None
        if role == 0:
            tret = 'baabc'
        return tret

class ListModel(qc.QAbstractItemModel):
    def __init__(self, parent):
        super().__init__(parent)
        # for i in range(10):
        #     self.insertRow(i, qg.QStandardItem("item-%d"%(i)))
        #     for j in range(10):
        #         pass
        self.rootIndex = self.createIndex(0, 0)
        self.loadingIcon = self.loadingIcon()
        self.cache_range = [0,0]
        self.count = 2000
        self.cd = {}
        self.loadingicon = qg.QIcon()
        for i in range(22):
            self.cd[i] = {}
        print(['create root', self.rootIndex])
    
    def loadingIcon(self):
        img = qg.QImage()
        img.load(os.path.join(os.path.dirname(__file__), 'loading.jpg'))
        pmp = qg.QPixmap()
        pmp.convertFromImage(img)
        return qg.QIcon(pmp)

    def index(self, row, column, parent=None):
        # print(['index', row, column, parent])
        if parent.isValid():
            return qc.QModelIndex()
        return self.createIndex(row, column)

    def parent(self, index):
        # print(['parent', index])
        return qc.QModelIndex()
    
    def rowCount(self, index=None):
        # print(['rowCount', index])
        if not index.isValid():
            return self.count
        return 0

    def columnCount(self, index=None):
        # print(['columnCount'])
        if not index.isValid():
            return 1
        return 0

    def data(self, index,role=None):
        row = index.row()
        # print(['data', row, index])
        if role == 0:
            return 'testb'
        elif role == 1:
            return self.loadingIcon

class ListDelegate(qw.QAbstractItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)
        self.paint_indexs = []
        self.image_cache = []
        self.bdColor = qg.QColor(12,24,24)
        self.bgColor = qg.QColor(12,12,24)
    
    def paint(self, painter, option, index):
        row = index.row()
        painter.setBrush(qg.QBrush(self.bdColor))
        painter.fillRect(option.rect,self.bgColor)
        painter.drawRect(option.rect)
        print(option.checkState)
        if row not in self.paint_indexs:
            self.paint_indexs.append(row)
        # print(['paint', self.paint_indexs])
    
    def sizeHint(self, opiton, index):
        return qc.QSize(400,400)

class Pagination(qw.QHBoxLayout):
    def __init__(self):
        super().__init__()
        self.__max_pnum = 1
        self.current_page_num = 1
        self.head = qw.QPushButton('<<')
        self.tail = qw.QPushButton('>>')
        self.prev = qw.QPushButton('<')
        self.next = qw.QPushButton('>')
        self.__label = qw.QLabel('1/1')
        self.addStretch(1)
        self.addWidget(self.head)
        self.addWidget(self.prev)
        self.addWidget(self.__label)
        self.addWidget(self.next)
        self.addWidget(self.tail)
        self.addStretch(1)
        self.update()
    
    def update(self):
        isinhead = self.current_page_num < 2
        isintail = self.current_page_num >= self.__max_pnum
        self.head.setEnabled(not isinhead)
        self.prev.setEnabled(not isinhead)
        self.__label.setText('%d/%d'%(self.current_page_num, self.__max_pnum))
        self.tail.setEnabled(not isintail)
        self.next.setEnabled(not isintail)

    def setMax(self, v):
        self.__max_pnum = v
        self.update()

    def setCurrent(self, v):
        self.current_page_num = v
        self.update()
    
    def setVisible(self, v):
        for each in (self.head, self.prev, self.__label, self.next, self.tail):
            each.setVisible(v)


class ImageLabel(qw.QLabel):
    def __init__(self,parent=None):
        super().__init__(parent)
        # self.setScaledContents(True)
        self.setSizePolicy(qw.QSizePolicy.Expanding, qw.QSizePolicy.Expanding)
        self.setAlignment(qc.Qt.AlignCenter)
        self.setMinimumSize(10,10)
        self.setMaximumSize(1024,1024)
        self.pixmap = None

    def setSourcePixmap(self, pixmap):
        self.pixmap = pixmap
        super().setPixmap(pixmap.scaled(self.size(),qc.Qt.KeepAspectRatio))

    def resizeEvent(self, event):
        if self.pixmap:
            scaled_pixmap = self.pixmap.scaled(event.size(), qc.Qt.KeepAspectRatio, qc.Qt.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
        super().resizeEvent(event)

class DPanel(qw.QDockWidget):
    def __init__(self):
        super().__init__()
        self.setTitleBarWidget(qw.QWidget())
        self.setWidget(qw.QWidget())
        # self.setStyleSheet('background-color:#325221;')
        mlay = qw.QVBoxLayout()
        self.widget().setLayout(mlay)
        self.pimg = ImageLabel()
        mlay.addWidget(self.pimg)
        self.name = qw.QLineEdit()
        self.name.setReadOnly(True)
        self.name.setMinimumHeight(38)
        self.name.setStyleSheet('color:#efefef;font-size:32px')
        mlay.addWidget(self.name)
        self.desc = qw.QTextEdit()
        self.desc.setReadOnly(True)
        self.desc.setMaximumHeight(88)
        self.desc.setStyleSheet('color:#afafaf;')
        mlay.addWidget(self.desc)
        self.tags = qw.QLineEdit()
        self.tags.setReadOnly(True)
        self.tags.setStyleSheet('color:#efefef;background-color:#5a5a5a;')
        mlay.addWidget(self.tags)
    
    def updateData(self, _d):
        pmp = qg.QPixmap()
        pmp.load(_d['image'])
        self.pimg.setSourcePixmap(pmp)
        self.name.setText(_d['name'])
        self.desc.setText(_d['desc'])
        self.tags.setText(_d['tags'])

class BPanel(qw.QDockWidget):
    def __init__(self):
        super().__init__()
        self.setTitleBarWidget(qw.QWidget())
        self.setWidget(qw.QWidget())
        # self.setStyleSheet('background-color:#321281;')
        mlay = qw.QVBoxLayout()
        self.widget().setLayout(mlay)
        tw = qw.QRadioButton(u"我的收藏")
        self.fov = tw
        mlay.addWidget(tw)
        tw.setStyleSheet('background-color:#181818;padding:8px;border-radius:4px')
        tw = qw.QRadioButton(u"展示全部")
        tw.setChecked(1)
        mlay.addWidget(tw)
        tw.setStyleSheet('background-color:#181818;padding:8px;border-radius:4px')
        tw = GroupTree()
        self.groupTree = tw
        mlay.addWidget(tw)
        # mlay.addWidget(qw.QLabel('TEST ABCDEFG'))
    
    def isLocal(self):
        return self.fov.isChecked()

class GroupTree(qw.QTreeWidget):
    def __init__(self):
        super().__init__()
        self.data = []
        self.ws = []
        self.namemap = {}
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(qc.Qt.ContextMenuPolicy.CustomContextMenu)
    
    def loadData(self, _d):
        self.data = _d
        idd = {}
        self.clear()
        ct = 0
        for eline in _d:
            _id = eline[0]
            pid = eline[1]
            name = eline[2]
            tw = qw.QTreeWidgetItem()
            tw.setData(0,qc.Qt.ItemDataRole.UserRole, eline)
            tw.setText(0, name)
            self.namemap[name] = ct
            idd[_id] = tw
            if pid in idd:
                idd[pid].addChild(tw)
            ct += 1
        self.addTopLevelItem(idd[1])
        self.expandAll()

class MainListBox(qw.QListWidget):
    loadedOneItem = qc.Signal(int)
    def __init__(self):
        super().__init__()
        # self.setModel(ListModel(self))
        # self.setItemDelegate(ListDelegate(self))
        self.icon_data = []
        self.view_id = 0
        self.setViewMode(self.ViewMode.IconMode)
        self.setResizeMode(self.ResizeMode.Adjust)
        self.setDragDropMode(self.DragDropMode.NoDragDrop)
        self.setContextMenuPolicy(qc.Qt.ContextMenuPolicy.CustomContextMenu)
        self.setIconSize(qc.QSize(100,100))
        self.setGridSize(qc.QSize(128,128))
        self.loadedOneItem.connect(self.updateItemIcon)
        def fa():
            tf = r"V:\pipeline\houdini_env\LTHT\python3.9libs\asset_library\imgseqfiles.txt"
            with open(tf) as _f:
                for rline in _f:
                    spl = rline.split('|')
                    if spl[1] != 'f':
                        continue
                    fpath = spl[0]
                    pmap = qg.QPixmap()
                    pmap.load(fpath)
                    ic = qg.QIcon(pmap)
                    lwitem = qw.QListWidgetItem()
                    lwitem.setIcon(ic)
                    self.addItem(lwitem)
    
    def loadImages(self):
        tf = r"V:\pipeline\houdini_env\LTHT\python3.9libs\asset_library\imgseqfiles.txt"
        _d = []
        with open(tf) as _f:
            for rline in _f:
                spl = rline.split('|')
                if spl[1] != 'f':
                    continue
                fpath = spl[0]
                _d.append((os.path.basename(fpath),fpath))
        self.loadData(_d)

    def updateItemIcon(self, _i):
        itm = self.item(_i)
        if not itm:
            return
        pmp = qg.QPixmap()
        pmp.convertFromImage(self.icon_data[_i][0])
        itm.setIcon(qg.QIcon(pmp))

    def loadData(self, d):
        self.view_id = id(d)
        loadingimg = qg.QIcon(os.path.join(os.path.dirname(__file__), 'loading.jpg'))
        self.icon_data.clear()
        self.clear()
        for eline in d:
            iid = eline[0]
            name = eline[1]
            fpath = eline[2]
            pim = qg.QImage()
            litm = qw.QListWidgetItem(loadingimg, name)
            # litm.setSizeHint(qc.QSize(128,128))
            litm.setData(qc.Qt.ItemDataRole.UserRole, eline)
            self.addItem(litm)
            self.icon_data.append((pim, fpath, self.view_id))

        def loadimgs(vid, *args):
            # print('loadimgs start')
            for i in range(len(self.icon_data)):
                if i >= len(self.icon_data):
                    break
                ditm = self.icon_data[i]
                if ditm[2] != vid:
                    # print('view id change break')
                    break
                img = ditm[0]
                path = ditm[1]
                try:
                    img.load(path)
                    self.loadedOneItem.emit(i)
                except Exception as e:
                    print([e])
            # print('loadimgs end')

        bt = threading.Thread(target=loadimgs, args=(self.view_id,))
        # bt.run = loadimgs
        # self.bt.finished.connect(setItemsIcon)
        bt.start()
                
class FilePathLine(qw.QHBoxLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = self
        # self.setLayout(lay)
        self.text = qw.QLineEdit()
        lay.addWidget(self.text)
        self.button = qw.QPushButton('..')
        lay.addWidget(self.button)
        def bf():
            text = qw.QFileDialog.getOpenFileName(parent, u'选择')
            if not text:
                return
            self.text.setText(text[0])
        self.button.clicked.connect(bf)

class CEAssetDialog(qw.QDialog):
    def __init__(self, parent=None, idata={}):
        super().__init__(parent)
        mlay = qw.QVBoxLayout()
        self.__ui = {}
        self.__d = idata
        self.setLayout(mlay)
        self.setWindowTitle(u'创建资产')
        flay = qw.QFormLayout()
        mlay.addLayout(flay)
        tw = FilePathLine()
        tw.text.setText(self.__d.get('path',''))
        self.__ui['path'] = tw
        flay.addRow(u'资产路径', tw)
        tw = qw.QLineEdit(self.__d.get('name',''))
        self.__ui['name'] = tw
        flay.addRow(u'资产名称', tw)
        tw = qw.QTextEdit(self.__d.get('description',''))
        self.__ui['description'] = tw
        flay.addRow(u'资产描述', tw)
        tw = qw.QLineEdit(self.__d.get('tags',''))
        self.__ui['tags'] = tw
        flay.addRow(u'资产标记', tw)
        tw = FilePathLine()
        tw.text.setText(self.__d.get('image',''))
        self.__ui['image'] = tw
        def loadpv(_path):
            if not os.path.isfile(_path):
                return
            pmp = qg.QPixmap()
            # pmp.scaled(256, 256)
            pmp.load(_path)
            self.__ui['showImage'].setPixmap(pmp.scaled(256,256, qc.Qt.KeepAspectRatio))
        tw.text.textChanged.connect(loadpv)
        flay.addRow(u'预览图', tw)
        tw = qw.QLabel()
        self.__ui['showImage'] = tw
        flay.addRow(u'', tw)
        tblay = qw.QHBoxLayout()
        mlay.addLayout(tblay)
        tw = qw.QPushButton(u'OK')
        def okf():
            def rep(msg):
                qw.QMessageBox.warning(self, 'Warning', msg)
            self.__d['path'] = self.__ui['path'].text.text()
            self.__d['name'] = self.__ui['name'].text()
            self.__d['description'] = self.__ui['description'].toPlainText()
            self.__d['tags'] = self.__ui['tags'].text()
            self.__d['image'] = self.__ui['image'].text.text()
            if not os.path.isfile(self.__d['path']):
                rep(u'资产路径下找不到文件')
                return
            if os.path.splitext(self.__d['image'])[-1].lower() not in ('.jpg','.jpeg','.png'):
                rep(u'预览图仅支持 jpg png 格式')
                return
            if not os.path.isfile(self.__d['image']):
                rep(u'预览图路径下找不到文件')
                return
            self.accept()
        tw.clicked.connect(okf)
        tblay.addWidget(tw)
        tw = qw.QPushButton(u'Cancel')
        tw.clicked.connect(self.reject)
        tblay.addWidget(tw)


class MainWin(qw.QMainWindow):
    __instance = None
    def __init__(self):
        super().__init__(qw.QApplication.activeWindow())
        # self.bgt = BackgroundT({})
        self.proj = CoreProject()
        self.localdata = LocalData()
        self.selectedGroup = []
        self.uis = {}
        self.page_data = {'max':1, 'current':1, 'page_item_count': 1000, 'query_item_count':0}
        self.mainlist_load_from_search = False
        self.mainlist_source = "group" # group local search 
        self.importer = Importer()
        self.actions = {
            'openProject':qw.QAction(u'打开工程'),
            'createGroup':qw.QAction(u'创建分组'),
            'createAsset':qw.QAction(u'创建资产'),
            'changeAsset':qw.QAction(u'修改资产'),
            'addFavour':qw.QAction(u'加入收藏'),
            'import2Houdini':qw.QAction(u'导入到Houdini'),
            'import2Maya':qw.QAction(u'导入到Maya'),
        }
        self.actions['openProject'].triggered.connect(self.openProjectAC)
        self.actions['createGroup'].triggered.connect(self.createGroupAC)
        self.actions['createAsset'].triggered.connect(self.createAssetAC)
        self.actions['changeAsset'].triggered.connect(self.changeAssetAC)
        self.actions['addFavour'].triggered.connect(self.addFavour)
        self.actions['import2Houdini'].triggered.connect(lambda: self.importer.import_houdini(self.mainlist.selectedItems()[0].data(qc.Qt.ItemDataRole.UserRole)[3]))
        self.actions['import2Maya'].triggered.connect(lambda: self.importer.import_maya(self.mainlist.selectedItems()[0].data(qc.Qt.ItemDataRole.UserRole)[3]))
        self.actions['createGroup'].setDisabled(True)
        self.actions['createAsset'].setDisabled(True)
        self.actions['changeAsset'].setDisabled(True)
        self.actions['addFavour'].setDisabled(True)
        self.actions['import2Houdini'].setDisabled(True)
        self.actions['import2Maya'].setDisabled(True)

        self.setWindowTitle(u"马虎资产库")
        self.setupMenuBar()
        self.setupToolBar()
        self.setupStatusBar()
        self.mainlist = MainListBox()
        self.mainlist.itemSelectionChanged.connect(self.onSelectedAssetChanged)
        self.mainlist.customContextMenuRequested.connect(self.showAssetContentMenu)
        tw = qw.QWidget()
        tlay = qw.QVBoxLayout()
        tlay.addWidget(self.mainlist)
        # tlay.addWidget(qw.QLabel(u'上一页 当前页 下一页'))
        self.pagination = Pagination()
        def headbfn():
            self.page_data['current'] = 1
            self.pagination.setCurrent(self.page_data['current'])
            self.loadMainListFromGid()
        self.pagination.head.clicked.connect(headbfn)
        def prevbfn():
            self.page_data['current'] -= 1
            self.pagination.setCurrent(self.page_data['current'])
            self.loadMainListFromGid()
        self.pagination.prev.clicked.connect(prevbfn)
        def nextbfn():
            self.page_data['current'] += 1
            self.pagination.setCurrent(self.page_data['current'])
            self.loadMainListFromGid()
        self.pagination.next.clicked.connect(nextbfn)
        def tailbfn():
            self.page_data['current'] = self.page_data['max']
            self.pagination.setCurrent(self.page_data['current'])
            self.loadMainListFromGid()
        self.pagination.tail.clicked.connect(tailbfn)
        tlay.addLayout(self.pagination)
        tw.setLayout(tlay)
        self.setCentralWidget(tw)
        self.bpan = BPanel()
        self.bpan.groupTree.customContextMenuRequested.connect(self.showGroupContentMenu)
        self.bpan.fov.toggled.connect(self.onFavourChanged)
        self.bpan.groupTree.itemSelectionChanged.connect(self.onSelectedGroupChanged)
        self.addDockWidget(qc.Qt.LeftDockWidgetArea, self.bpan)
        self.dpan = DPanel()
        self.addDockWidget(qc.Qt.RightDockWidgetArea, self.dpan)

        self.localdata.load()
        if self.localdata['recent']:
            self.openProject(self.localdata['recent'][0])
            self.addRecentFile(self.localdata['recent'][0])
            self.updateRecentMenu(self.localdata['recent'])
    
    def setupMenuBar(self):
        bb = qw.QMenuBar()
        fm = bb.addMenu(u"文件")
        # test_a = fm.addAction("TEST")
        # def tfn():
        #     print("test action clicked")
        #     return
        #     self.centralWidget().loadImages()
        #     self.statusBar().showMessage("test action clicked", 16000)
        #     print(self.statusBar().size())
        #     print(self.thread())
        # test_a.triggered.connect(tfn)
        # test_a = fm.addAction('TEST import lib imgs')
        # test_a.triggered.connect(self.importlibtestfn)
        op = fm.addAction(self.actions['openProject'])
        fm.addAction(op)
        op = fm.addMenu(u"打开最近的工程")
        self.uis['openRecentMenu'] = op
        fm.addMenu(op)
        op = fm.addAction(u"检验是否拥有写入权限")
        def cwfn():
            if self.proj.exists():
                if self.proj.canIWrite():
                    qw.QMessageBox.information(self, u"Info", u"拥有写入权限")
                else:
                    self.warningCanNotWrite()
            else:
                self.warningNoProject()
        op.triggered.connect(cwfn)
        fm.addAction(op)
        # em = bb.addMenu(u"编辑")
        am = bb.addMenu(u"关于")
        va = am.addAction(u"版本")
        va.triggered.connect(lambda:qw.QMessageBox.information(self,u'版本信息','Version : '+MHLIB_VERSION+'\nAuthor : PengChenge'))
        self.setMenuBar(bb)

    def updateRecentMenu(self, files):
        mu = self.uis['openRecentMenu']
        mu.clear()
        def gf(ff):
            def fn():
                self.openProject(ff)
            return fn
        for ff in files:
            ac = mu.addAction(ff)
            ac.triggered.connect(gf(ff))

    def setupToolBar(self):
        bb = qw.QToolBar()
        bb.setFloatable(False)
        bb.setMovable(False)
        bb.setFixedHeight(48)
        # bb.addAction(self.actions['createGroup'])
        # bb.addAction(self.actions['createAsset'])
        tw = qw.QLineEdit()
        self.uis['search'] = tw
        tw.textChanged.connect(self.onSearchTextChanged)
        tw.setStyleSheet('margin:0 0 0 22;')
        tw.setMaximumSize(256,28)
        tw.setPlaceholderText(u'Search')
        bb.addWidget(tw)
        self.addToolBar(bb)

    def updateMainListSource(self):
        if self.bpan.isLocal():
            self.mainlist_source = "local"
            return
        elif self.uis['search'].text():
            self.mainlist_source = "search"
            return
        else:
            self.mainlist_source = "group"

    def setupStatusBar(self):
        bb = qw.QStatusBar()
        self.setStatusBar(bb)
    
    def showGroupContentMenu(self, pos):
        contextMenu = qw.QMenu(self)
        contextMenu.addAction(self.actions['createGroup'])
        contextMenu.exec_(self.bpan.groupTree.mapToGlobal(pos))

    def showAssetContentMenu(self, pos):
        contextMenu = qw.QMenu(self)
        if self.mainlist_source == 'group':
            contextMenu.addAction(self.actions['createAsset'])
            contextMenu.addAction(self.actions['changeAsset'])
            contextMenu.addAction(self.actions['addFavour'])
        contextMenu.addAction(self.actions['import2Houdini'])
        contextMenu.addAction(self.actions['import2Maya'])
        contextMenu.exec_(self.mainlist.mapToGlobal(pos))

    def openProject(self, _path):
        if not os.path.isdir(_path):
            return
        proj = CoreProject()
        proj.setRootPath(_path)
        if not proj.exists():
            return
        self.proj = proj
        self.addRecentFile(_path)
        self.loadGroup()
        wable = proj.canIWrite()
        self.actions['createGroup'].setEnabled(wable)
        self.actions['createAsset'].setEnabled(wable)
        self.setWindowFilePath(_path)
        self.setWindowTitle(u'马虎资产库 - '+_path)

    def addRecentFile(self, _path):
        recs = self.localdata['recent']
        if recs:
            nrecs = [_path]
            for epath in recs:
                if epath not in nrecs:
                    nrecs.append(epath)
                if len(nrecs) > 6:
                    break
            self.localdata['recent'] = nrecs
        else:
            self.localdata['recent'] = [_path]

    def openProjectAC(self):
        sel = qw.QFileDialog.getExistingDirectory(self, u'选择工程文件夹')
        if not sel:
            return
        proj = CoreProject()
        proj.setRootPath(sel)
        self.proj = proj
        if not proj.exists():
            # create
            lk = proj.getLock()
            lk.lock()
            if not lk.haslock:
                qw.QMessageBox.warning(self,'Warning',u'没有写权限')
                return
            proj.create()
            lk.unlock()
        self.addRecentFile(sel)
        self.updateRecentMenu(self.localdata['recent'])
        self.loadGroup()
        self.setWindowFilePath(sel)
        self.setWindowTitle(u'马虎资产库 - '+sel)

    def createGroupAC(self):
        if not self.proj.canIWrite():
            self.warningCanNotWrite()
            return
        trw = self.bpan.groupTree
        selms = trw.selectedItems()
        if not selms:
            self.warningNoSelectedGroup()
            return
        print(selms)
        seld = trw.data[trw.namemap[selms[0].text(0)]]
        print(seld)
        inp = qw.QInputDialog.getText(self, u'输入组命名', u'组名')
        if not inp:
            return
        if not inp[1]:
            return
        if not re.match('^[_A-Za-z]+$', inp[0]):
            self.warningGroupNameError()
            return
        if inp[0] in trw.namemap:
            self.warningGroupNameRepeat()
            return
        lk = self.proj.getLock()
        lk.lock()
        if not lk.haslock:
            self.warningDatabaseLock()
            return
        conn = sqlite3.connect(self.proj.asset_db)
        conn.execute('INSERT OR REPLACE INTO group_db (id,pid,name) VALUES (?,?,?)', (hash(inp), seld[0], inp[0]))
        conn.commit()
        conn.close()
        lk.unlock()
        self.loadGroup()

    def createAssetAC(self):
        data = {}
        crd = CEAssetDialog(self, data)
        if not crd.exec_():
            return
        iid = hash(data['path']+data['name'])
        pid = self.selectedGroup[0]
        iconpath = '/'.join(CoreUtilities.hashstr(data['image']))+'.jpg'
        iconfullpath = os.path.join(self.proj.thumbs_dir, iconpath)
        lk = self.proj.getLock()
        lk.lock()
        if not lk.haslock:
            self.warningDatabaseLock()
            return
        if not os.path.isfile(iconfullpath):
            tmp = os.path.dirname(iconfullpath)
            if not os.path.isdir(tmp):
                os.makedirs(tmp)
            pmp = qg.QPixmap()
            pmp.load(data['image'])
            pmp.scaled(128,128).save(iconfullpath, 'JPG', 92)
        conn = sqlite3.connect(self.proj.asset_db)
        conn.execute(
            'INSERT OR REPLACE INTO asset_db (id,path,name,description,gid,thumbl,thumbh) VALUES (?,?,?,?,?,?,?)',
            (iid,data['path'],data['name'],data['description'],pid,iconpath,data['image'])
            )
        conn.commit()
        conn.close()
        tags = []
        atlink = []
        for each in set(re.split(u'[, ，]', data['tags']+','+data['name'])):
            if not each:
                continue
            tag_id = hash(each)
            tags.append((tag_id,each))
            atlink.append((iid,tag_id))
        if tags:
            conn = sqlite3.connect(self.proj.index_db)
            conn.executemany(
                'INSERT OR REPLACE INTO tags (id,tag) VALUES (?,?)',
                tags
            )
            conn.commit()
            conn.executemany(
                'INSERT OR REPLACE INTO taglink (asset_id,tag_id) VALUES (?,?)',
                atlink
            )
            conn.commit()
            conn.close()
        lk.unlock()
        self.loadMainListFromGid()

    def changeAssetAC(self):
        itdata = self.mainlist.selectedItems()[0].data(qc.Qt.ItemDataRole.UserRole)
        conn = sqlite3.connect(CoreUtilities.sqlReadOnlyConnect(self.proj.asset_db),uri=True)
        qd = conn.execute('SELECT id,path,name,description,thumbh FROM asset_db WHERE id = ?', [itdata[0]]).fetchone()
        conn.close()
        data = {
            'id':qd[0],
            'path':qd[1],
            'name':qd[2],
            'description':qd[3],
            'image':qd[4],
        }
        conn = sqlite3.connect(CoreUtilities.sqlReadOnlyConnect(self.proj.index_db),uri=True)
        qd = conn.execute('SELECT tag_id FROM taglink WHERE asset_id = ?', [itdata[0]]).fetchall() or []
        conn.close()
        utags = []
        if qd:
            for qline in qd:
                conn = sqlite3.connect(CoreUtilities.sqlReadOnlyConnect(self.proj.index_db),uri=True)
                qd = conn.execute('SELECT tag FROM tags WHERE id = ?', [qline[0]]).fetchone()
                if qd:
                    utags.append(qd[0])
                conn.close()
        data['tags'] = ' '.join(utags)
        dlg = CEAssetDialog(self, data)
        if not dlg.exec_():
            return
        iid = data['id']
        pid = self.selectedGroup[0]
        iconpath = '/'.join(CoreUtilities.hashstr(data['image']))+'.jpg'
        iconfullpath = os.path.join(self.proj.thumbs_dir, iconpath)
        lk = self.proj.getLock()
        lk.lock()
        if not lk.haslock:
            self.warningDatabaseLock()
            return
        if not os.path.isfile(iconfullpath):
            tmp = os.path.dirname(iconfullpath)
            if not os.path.isdir(tmp):
                os.makedirs(tmp)
            pmp = qg.QPixmap()
            pmp.load(data['image'])
            pmp.scaled(128,128).save(iconfullpath, 'JPG', 92)
        conn = sqlite3.connect(self.proj.asset_db)
        conn.execute(
            'UPDATE asset_db set path=?,name=?,description=?,gid=?,thumbl=?,thumbh=? WHERE id = ?',
            (data['path'],data['name'],data['description'],pid,iconpath,data['image'], iid)
            )
        conn.commit()
        conn.close()
        tags = []
        atlink = []
        for each in set(re.split(u'[, ，]', data['tags']+','+data['name'])):
            if not each:
                continue
            tag_id = hash(each)
            tags.append((tag_id,each))
            atlink.append((iid,tag_id))
        if tags:
            conn = sqlite3.connect(self.proj.index_db)
            cur = conn.cursor()
            cur.execute('DELETE FROM taglink WHERE asset_id = ?', [iid])
            conn.commit()
            cur.executemany(
                'INSERT OR REPLACE INTO tags (id,tag) VALUES (?,?)',
                tags
            )
            conn.commit()
            conn.executemany(
                'INSERT OR REPLACE INTO taglink (asset_id,tag_id) VALUES (?,?)',
                atlink
            )
            conn.commit()
            conn.close()
        lk.unlock()
        self.loadMainListFromGid()

    def loadGroup(self):
        conn = sqlite3.connect(CoreUtilities.sqlReadOnlyConnect(self.proj.asset_db), uri=1)
        datas = conn.execute("SELECT id,pid,name FROM group_db").fetchall()
        conn.close()
        self.bpan.groupTree.loadData(datas)

    def onFavourChanged(self, favchecked):
        self.bpan.groupTree.setDisabled(favchecked)
        self.updateMainListSource()
        self.loadMainListFromStatus()

    def onSearchTextChanged(self):
        self.updateMainListSource()
        self.loadMainListFromStatus()
    
    def loadMainListFromLocal(self):
        if not self.localdata["lids"]:
            self.localdata["lids"] = []
        datas = []
        if self.localdata["lids"]:
            conn = sqlite3.connect(CoreUtilities.sqlReadOnlyConnect(self.proj.asset_db),uri=True)
            for aid in self.localdata["lids"]:
                ceq = conn.execute('SELECT id,name,thumbl,path FROM asset_db WHERE id = ?', [aid]).fetchone()
                if ceq:
                    datas.append((ceq[0],ceq[1],os.path.join(self.proj.thumbs_dir, ceq[2]),ceq[3]))
            conn.close()
        self.mainlist.loadData(datas)

    def loadMainListFromSearch(self):
        setext = self.uis['search'].text()
        datas = []
        qaids = []
        conn = sqlite3.connect(CoreUtilities.sqlReadOnlyConnect(self.proj.index_db),uri=True)
        ceq = conn.execute('SELECT id FROM tags WHERE tag LIKE ?', [setext+'%']).fetchone()
        if ceq:
            tagid = ceq[0]
            ceq = conn.execute('SELECT asset_id FROM taglink WHERE tag_id = ? LIMIT 16', [tagid]).fetchall()
            if ceq:
                qaids = list(map(lambda x:x[0], ceq))
        conn.close()
        if qaids:
            conn = sqlite3.connect(CoreUtilities.sqlReadOnlyConnect(self.proj.asset_db),uri=True)
            for aid in qaids:
                ceq = conn.execute('SELECT id,name,thumbl,path FROM asset_db WHERE id = ?', [aid]).fetchone()
                if ceq:
                    datas.append((ceq[0],ceq[1],os.path.join(self.proj.thumbs_dir, ceq[2]),ceq[3]))
            conn.close()
        self.mainlist.loadData(datas)

    def loadMainListFromStatus(self):
        if self.mainlist_source == "group":
            if self.selectedGroup:
                self.page_data['current'] = 1
                conn = sqlite3.connect(CoreUtilities.sqlReadOnlyConnect(self.proj.asset_db),uri=True)
                self.page_data['query_item_count'] = conn.execute('SELECT COUNT(id) FROM asset_db WHERE gid = ?',[self.selectedGroup[0]]).fetchone()[0]
                conn.close()
                import math
                self.page_data['max'] = math.ceil(float(self.page_data['query_item_count'])/float(self.page_data['page_item_count']))
                self.pagination.setMax(self.page_data['max'])
                self.pagination.setCurrent(self.page_data['current'])
                self.pagination.setVisible(True)
                self.loadMainListFromGid()
            else:
                self.mainlist.loadData([])
        elif self.mainlist_source == "search":
            self.pagination.setVisible(False)
            self.loadMainListFromSearch()
        elif self.mainlist_source == "local":
            self.pagination.setVisible(False)
            self.loadMainListFromLocal()

    def loadMainListFromGid(self):
        gid = self.selectedGroup[0]
        conn = sqlite3.connect(CoreUtilities.sqlReadOnlyConnect(self.proj.asset_db),uri=True)
        datas = conn.execute('SELECT id,name,thumbl,path FROM asset_db WHERE gid = ? LIMIT %d OFFSET %d'%(
            self.page_data['page_item_count'], ((self.page_data['current']-1)*self.page_data['page_item_count'])
            ), [gid]).fetchall()
        conn.close()
        self.mainlist.loadData(map(lambda x:[x[0],x[1],os.path.join(self.proj.thumbs_dir, x[2]),x[3]], datas))

    def onSelectedGroupChanged(self):
        sels = self.bpan.groupTree.selectedItems()
        hassel = bool(sels)
        _en = hassel and self.proj.canIWrite()
        self.actions['createGroup'].setEnabled(_en)
        self.actions['createAsset'].setEnabled(_en)
        if hassel:
            self.selectedGroup = sels[0].data(0,qc.Qt.ItemDataRole.UserRole)
        self.loadMainListFromStatus()

    def onSelectedAssetChanged(self):
        sels = self.mainlist.selectedItems()
        self.actions['changeAsset'].setEnabled(len(sels) > 0)
        self.actions['addFavour'].setEnabled(len(sels) > 0)
        self.actions['import2Houdini'].setEnabled(self.importer.app == 'HOUDINI' and len(sels) > 0)
        self.actions['import2Maya'].setEnabled(self.importer.app == 'MAYA' and len(sels) > 0)
        if not sels:
            return
        selid = sels[0].data(qc.Qt.ItemDataRole.UserRole)[0]
        _d = {}
        with sqlite3.connect(CoreUtilities.sqlReadOnlyConnect(self.proj.asset_db), uri=True) as conn:
            qd = conn.execute('SELECT name,description,thumbh FROM asset_db WHERE id = ?', [selid]).fetchone()
        if not qd:
            return
        _d['name'] = qd[0]
        _d['desc'] = qd[1]
        _d['image'] = qd[2]
        tags = []
        tagids = []
        with sqlite3.connect(CoreUtilities.sqlReadOnlyConnect(self.proj.index_db), uri=True) as conn:
            tagids = conn.execute('SELECT tag_id FROM taglink WHERE asset_id = ? limit 32', [selid]).fetchall()
        with sqlite3.connect(CoreUtilities.sqlReadOnlyConnect(self.proj.index_db), uri=True) as conn:
            for iid in tagids:
                qd = conn.execute('SELECT tag FROM tags WHERE id = ?', [iid[0]]).fetchone()
                if qd and qd[0] != _d['name']:
                    tags.append(qd[0])
        _d['tags'] = ' '.join(tags)
        self.dpan.updateData(_d)

    def addFavour(self):
        fds = self.localdata["lids"] or []
        fds.append(self.mainlist.selectedItems()[0].data(qc.Qt.ItemDataRole.UserRole)[0])
        self.localdata["lids"] = fds[:]

    def warningNoProject(self):
        qw.QMessageBox.warning(self, 'warning', u'当前工程不可用')

    def warningCanNotWrite(self):
        qw.QMessageBox.warning(self, 'warning', u'没有写入权限')

    def warningDatabaseLock(self):
        qw.QMessageBox.warning(self, 'warning', u'数据库被锁定')

    def warningBackgroundBusy(self):
        qw.QMessageBox.warning(self, 'warning', u'后台进程正忙')

    def warningNoSelectedGroup(self):
        qw.QMessageBox.warning(self, 'warning', u'当前未选择分组')

    def warningGroupNameError(self):
        qw.QMessageBox.warning(self, 'warning', u'组命名不正确')

    def warningGroupNameRepeat(self):
        qw.QMessageBox.warning(self, 'warning', u'组名重复')

    def importlibtestfn(self):
        print('def importlibtestfn(self):')
        maxlimit = 3000
        ct = 0
        imgpaths = []
        tagins = []
        taglinkins = []
        with open (r"V:\pipeline\houdini_env\LTHT\python3.9libs\asset_library\imgfs.txt") as _f:
            for eline in _f:
                sp = eline.split('|')
                fpath = sp[0]
                ftype = sp[1]
                fname = os.path.basename(fpath)
                fnamexext = os.path.splitext(fname)
                if ftype != 'f':
                    continue
                if fnamexext[-1].lower() not in ('.jpg','.jpeg','.png'):
                    continue
                aname = fnamexext[0]
                aid = hash(fpath)
                lpath = '/'.join(CoreUtilities.hashstr(fpath))+'.jpg'
                lfpath = os.path.join(self.proj.thumbs_dir, lpath)
                if not os.path.isfile(lfpath):
                    _d = os.path.dirname(lfpath)
                    if not os.path.isdir(_d):
                        os.makedirs(_d)
                    CoreUtilities.convertLowImage(fpath,lfpath)
                imgpaths.append((aid,1,aname,fpath,lpath,fpath))
                tagn = aname
                tagid = hash(tagn)
                tagins.append((tagid, tagn))
                taglinkins.append((aid,tagid))
                if ct > maxlimit:
                    break
                ct += 1
        conn = sqlite3.connect(self.proj.asset_db)
        cur = conn.cursor()
        cur.executemany('INSERT OR REPLACE INTO asset_db (id,gid,name,path,thumbl,thumbh) VALUES (?,?,?,?,?,?)', imgpaths)
        conn.commit()
        conn.close()
        conn = sqlite3.connect(self.proj.index_db)
        cur = conn.cursor()
        cur.executemany('INSERT OR REPLACE INTO tags (id,tag) VALUES (?,?)', tagins)
        conn.commit()
        cur.executemany('INSERT OR REPLACE INTO taglink (asset_id,tag_id) VALUES (?,?)', taglinkins)
        conn.commit()
        conn.close()
        print(['def importlibtestfn(self):', len(imgpaths)])

    @staticmethod
    def Run_():
        i = MainWin.__instance
        if i is not None:
            i.deleteLater()
        i = MainWin()
        MainWin.__instance = i
        i.show()