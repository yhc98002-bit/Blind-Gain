import json,os,stat,sys,time
d=sys.argv[1]; uid=os.getuid(); out=[]
for name in sorted(os.listdir(d)):
    p=os.path.join(d,name)
    try: st=os.lstat(p)
    except OSError: continue
    if st.st_uid!=uid: continue
    tot=0
    if stat.S_ISDIR(st.st_mode):
        for r,ds,fs in os.walk(p,followlinks=False):
            for n in fs:
                try: tot+=os.lstat(os.path.join(r,n)).st_size
                except OSError: pass
    else: tot=st.st_size
    out.append((tot,time.strftime("%m-%d %H:%M",time.gmtime(st.st_mtime)),p))
out.sort(reverse=True)
print(json.dumps([p for _,_,p in out]))
sys.stderr.write("total %.2f GiB across %d entries\n"%(sum(t for t,_,_ in out)/1024**3,len(out)))
for t,m,p in out: sys.stderr.write("  %9.3f GiB  %s  %s\n"%(t/1024**3,m,p))
