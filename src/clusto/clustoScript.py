import libDigg
import csParse
import time
import os

class Script:

    def __init__(self,cs):
        """ create the task object?"""

        self.csDict = cs.clusterScript

    def createChunks(self):

        mydict = self.csDict
        chunks = []

        for keys in mydict.keys():
            if keys == "globalHeader":
                globals = mydict[keys]

        for objects in mydict.values():
            chunk = Chunk(objects)
            chunk.setGlobals(globals)
            chunks.append(chunk)

        self.chunks = chunks

    def resolveChunks(self):

        # resolve the chunk and add the resolved Task to the Chunk
        # I'm faking it here until the resolver is done
        # should this be here, or in Chunks class?
            

        tasks = []
        for c in self.chunks:
            # skip the special header chunk
            if c.tasknum == 0:
                continue
            # make up some bullshit resolved tasks for now and attach them to a chunk
            # even though the real parsed in task might not look anything like this

            for i in 1,2,3:
                mydict = {'name':'testing chunk','body':['echo "blah blah"\n', 'ls /trlkaijs'], 'shell':'bash', 'services_include':'32G', 'runmode':'hostwithrole', 'task':2, 'cluster_root':'/foo', 'services':'foo1-3', 'mykey':'myvalue', 'ip':'127.0.0.1', 'transport':'ssh', 'onError':'continue' , 'maxParallel':'10' , 'debug':0,'verbose':1}
                t = Task(i,mydict)
                tasks.append(t)

            c.tasks = tasks
            tasks = []

class Chunk:

    def __init__(self,object):

        self.chunk = object
        self.tasknum = object['task']
        self._setDefaults()

    def _setDefaults(self):
    
        # add other defaults here. maybe get them from the database?
        # FIXME default user root? no good
        defaults = { 'user':'root' , 'shell':'bash' ,'transport':'ssh' , 'onError':'continue' , 'maxParallel':'10', 'verbose':'1' }
        
        mydict = self.chunk

        # if the key does not exist in the task, add a default key
        for k in defaults.keys():
            if not mydict.has_key(k):
                mydict[k]=defaults[k]    

    def setGlobals(self,globals):
        """take the globals dict and copy in any values that are missing or not overridden"""
        mydict = self.chunk

        for k in globals.keys():
            if not mydict.has_key(k):
                mydict[k]=globals[k]


class Task:

    def __init__(self,num,dict):
        # this is not real for now. the resolver will ultimatley have to do the lifting here to 
        # create the task objects when they are fully resolved.
        # that's why this looks so sad

        self.tasknum=num
        self.task=dict

class QueueRunner:

    def __init__(self,chunk):
        """takes a chunk that has resolved tasks in a list attached to it"""
        self.chunk = chunk 
        t = chunk.tasks[0]

        # set some defaults at the queue level
        # we'll just take them from the first task

        self.shell = t.task['shell']
        self.onError = t.task['onError']
        self.transport = t.task['transport']
        self.maxParallel = t.task['maxParallel']
        self.debug = t.task['debug']
        self.name = t.task['name']
        self.verbose = t.task['verbose']
        self.user = t.task['user']

    def writeTasks(self):

        """write out each task into a tempfile"""
        for t in self.chunk.tasks:
            fname = libDigg.tempFile()
            t.tempFile = fname
            # sleep a tiny bit to make sure the filename is unique
            time.sleep(.25)
            f = libDigg.fopen(fname,'w')
            body = t.task['body']
            for line in body:
                f.write(line)
            status = f.close()

            if status != None:
                print "writing temp file failed: %s" % status

    def execute(self):

        """copy each temp script to the proper host and execute each task"""

        for t in self.chunk.tasks:

            if not self.transport == "ssh":
                print "transport method %s not yet implimented" % self.transport    
                sys.exit()

            # note that this is not any kind of real fork (yet)
            # and is really only doing the tasks serially
            # also note that there is no kind of timeout alarm set 
            # to kill problem tasks

            chunknum = self.chunk.tasknum
            ip = t.task['ip']
            runningTasks = 0

            if runningTasks < self.maxParallel:

                runningTasks+=1
                if not self.verbose == 0:
                    print "starting chunk %s task %s on %s" % (chunknum,t.tasknum,ip)

                # pass the task to the queue
                self._queue(t)
            else:
                # is this the right way to do this?
                if not self.verbose == 0:
                    print "task %s waiting for queue to flush" % t.tasknum
                os.sleep(30)

            runningTasks-=1

    def _queue(self,t):    

        # first, push out each script            
        host = t.task['ip']
        user = "root"
        print "scp %s %s@%s:/tmp" % (t.tempFile,user,host)
        tmpCmd = "scp %s %s@%s:/tmp" % (t.tempFile,user,host)
        tmpPipe = os.popen(tmpCmd)
        t.tmpCopy = tmpPipe.readlines()
        tmpExit = tmpPipe.close()
        ip = t.task['ip']
                        
        if tmpExit == None:
            t.tmpExit = 0
        else:
            t.tmpExit = tmpExit

        if not t.tmpExit == 0:
            print "copying script to %s unsuccessful" % ip
            print t.tmpCopy
            print t.tmpExit
            os.exit()

        # then run each task
        cmd = "ssh %s@%s %s %s " % (self.user,host,self.shell,t.tempFile)
        cmdPipe = os.popen(cmd)
        t.cmdRun = cmdPipe.readlines()
        t.cmdExit = cmdPipe.close()

        if t.cmdExit == None:
            t.cmdExit = 0
        else:
            t.cmdExit = tmpExit

        if not t.cmdExit == 0:
            print "running script on %s unsuccessful: %s" % (ip,t.tempFile)
            print t.cmdRun
            print t.cmdExit
            if not self.onError == "continue":
                os.exit()

        if not self.verbose == 0:
            for line in t.cmdRun:
                print line

    def cleanUp(self):

        """if debug is off, delete the tempfiles on the local machine"""

        if self.debug == 0:
            for t in self.chunk.tasks:
                os.unlink(t.tempFile)


if __name__ == '__main__':

    filename = "clusterscript.cs"
    cs = parseCs.parseCsFile(filename)
    cs.parseCsHeader()
    cs.parseTasks()

    script = Script(cs)
    script.createChunks()
    script.resolveChunks()

    for chunk in script.chunks:

        # skip the first chunk
        # which is just the global header data
        if chunk.tasknum == 0:
            continue
        q = QueueRunner(chunk)
        q.writeTasks()
        q.execute()
        #q.cleanUp()
        
    
