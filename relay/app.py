from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from .http_client import RelayError, parse_key_value_lines, perform_request, to_curl
from .mock_server import MockResponse, MockServer
from .models import RequestSpec
from .storage import RelayStore

BG="#0b0f14"; PANEL="#121820"; PANEL_2="#18212b"; TEXT="#edf3f7"; MUTED="#8796a5"; ACCENT="#46a8ff"; GREEN="#67e8a5"; RED="#ff6b73"

class RelayApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__(); self.title("Relay — local HTTP client"); self.geometry("1180x760"); self.minsize(900,620); self.configure(bg=BG)
        self.store=RelayStore(); self.mock=MockServer(logger=self._mock_log); self._style(); self._build(); self._refresh_sidebar(); self.protocol("WM_DELETE_WINDOW", self._close)

    def _style(self):
        s=ttk.Style(self); s.theme_use("clam"); s.configure("TFrame",background=BG); s.configure("Panel.TFrame",background=PANEL); s.configure("TLabel",background=BG,foreground=TEXT,font=("Segoe UI",10)); s.configure("Muted.TLabel",background=BG,foreground=MUTED); s.configure("Title.TLabel",background=BG,foreground=TEXT,font=("Segoe UI Semibold",22)); s.configure("TButton",background=PANEL_2,foreground=TEXT,borderwidth=0,padding=(12,8)); s.map("TButton",background=[("active","#22303d")]); s.configure("Accent.TButton",background=ACCENT,foreground="#06111a",padding=(16,9),font=("Segoe UI Semibold",10)); s.configure("TCombobox",fieldbackground=PANEL_2,background=PANEL_2,foreground=TEXT,arrowcolor=TEXT); s.configure("TNotebook",background=BG,borderwidth=0); s.configure("TNotebook.Tab",background=PANEL,foreground=MUTED,padding=(14,8),borderwidth=0); s.map("TNotebook.Tab",background=[("selected",PANEL_2)],foreground=[("selected",TEXT)]); s.configure("Treeview",background=PANEL,fieldbackground=PANEL,foreground=TEXT,rowheight=28,borderwidth=0); s.configure("Treeview.Heading",background=PANEL_2,foreground=MUTED,borderwidth=0); s.map("Treeview",background=[("selected","#18344d")])

    def _build(self):
        h=ttk.Frame(self); h.pack(fill="x",padx=22,pady=(18,8)); ttk.Label(h,text="Relay",style="Title.TLabel").pack(side="left"); ttk.Label(h,text="  HTTP client · inspector · mock server",style="Muted.TLabel").pack(side="left",pady=(8,0))
        root=ttk.Panedwindow(self,orient="horizontal"); root.pack(fill="both",expand=True,padx=18,pady=(0,18)); side=ttk.Frame(root,style="Panel.TFrame",width=245); main=ttk.Frame(root); root.add(side,weight=1); root.add(main,weight=5)
        tabs=ttk.Notebook(side); tabs.pack(fill="both",expand=True); hist=ttk.Frame(tabs,style="Panel.TFrame"); saved=ttk.Frame(tabs,style="Panel.TFrame"); tabs.add(hist,text="History"); tabs.add(saved,text="Saved")
        self.history_tree=ttk.Treeview(hist,columns=("status",),show="tree headings"); self.history_tree.heading("#0",text="Request"); self.history_tree.heading("status",text="Status"); self.history_tree.column("status",width=56,anchor="center"); self.history_tree.pack(fill="both",expand=True,padx=8,pady=8); self.history_tree.bind("<Double-1>",lambda _:self._load_history())
        self.saved_tree=ttk.Treeview(saved,show="tree"); self.saved_tree.heading("#0",text="Saved request"); self.saved_tree.pack(fill="both",expand=True,padx=8,pady=(8,4)); self.saved_tree.bind("<Double-1>",lambda _:self._load_saved()); ttk.Button(saved,text="Delete",command=self._delete_saved).pack(fill="x",padx=8,pady=(0,8))
        bar=ttk.Frame(main); bar.pack(fill="x",pady=(0,10)); self.method=tk.StringVar(value="GET"); ttk.Combobox(bar,textvariable=self.method,values=("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS"),state="readonly",width=9).pack(side="left",padx=(0,8),ipady=4); self.url=tk.StringVar(value="http://localhost:8765/"); e=tk.Entry(bar,textvariable=self.url,bg=PANEL_2,fg=TEXT,insertbackground=TEXT,relief="flat",font=("Segoe UI",11)); e.pack(side="left",fill="x",expand=True,ipady=8,padx=(0,8)); e.bind("<Return>",lambda _:self._send()); ttk.Button(bar,text="Send",style="Accent.TButton",command=self._send).pack(side="left")
        a=ttk.Frame(main); a.pack(fill="x",pady=(0,8)); ttk.Button(a,text="Save request",command=self._save_request).pack(side="left",padx=(0,6)); ttk.Button(a,text="Copy cURL",command=self._copy_curl).pack(side="left"); self.summary=ttk.Label(a,text="Ready",style="Muted.TLabel"); self.summary.pack(side="right")
        panes=ttk.Panedwindow(main,orient="vertical"); panes.pack(fill="both",expand=True); req=ttk.Frame(panes); resp=ttk.Frame(panes); panes.add(req,weight=2); panes.add(resp,weight=3)
        self.req_tabs=ttk.Notebook(req); self.req_tabs.pack(fill="both",expand=True); self.params_text=self._text_tab(self.req_tabs,"Params","# one per line\npage=1\nlimit=20"); self.headers_text=self._text_tab(self.req_tabs,"Headers","Accept: application/json"); self.body_text=self._text_tab(self.req_tabs,"Body",""); mock=ttk.Frame(self.req_tabs,style="Panel.TFrame"); self.req_tabs.add(mock,text="Mock server"); self._build_mock(mock)
        rt=ttk.Notebook(resp); rt.pack(fill="both",expand=True,pady=(10,0)); self.response_text=self._text_tab(rt,"Response",""); self.response_headers=self._text_tab(rt,"Headers","")

    def _text_tab(self,nb,title,initial):
        f=ttk.Frame(nb,style="Panel.TFrame"); nb.add(f,text=title); t=tk.Text(f,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief="flat",wrap="none",font=("Cascadia Mono",10),padx=12,pady=10); t.pack(fill="both",expand=True); t.insert("1.0",initial); return t

    def _build_mock(self,p):
        top=ttk.Frame(p,style="Panel.TFrame"); top.pack(fill="x",padx=12,pady=12); self.mock_port=tk.StringVar(value="8765"); self.mock_path=tk.StringVar(value="/"); self.mock_status=tk.StringVar(value="200")
        for label,var,width in (("Port",self.mock_port,8),("Path",self.mock_path,18),("Status",self.mock_status,6)):
            ttk.Label(top,text=label,background=PANEL).pack(side="left"); tk.Entry(top,textvariable=var,width=width,bg=PANEL_2,fg=TEXT,insertbackground=TEXT,relief="flat").pack(side="left",padx=(8,14),ipady=5)
        self.mock_button=ttk.Button(top,text="Start",command=self._toggle_mock); self.mock_button.pack(side="right"); ttk.Label(p,text="Response body",background=PANEL,foreground=MUTED).pack(anchor="w",padx=12); self.mock_body=tk.Text(p,height=7,bg=PANEL_2,fg=TEXT,insertbackground=TEXT,relief="flat",font=("Cascadia Mono",10),padx=10,pady=8); self.mock_body.pack(fill="both",expand=True,padx=12,pady=(6,8)); self.mock_body.insert("1.0",'{\n  "ok": true,\n  "source": "Relay mock"\n}'); self.mock_log=tk.Text(p,height=4,bg="#0e141b",fg=MUTED,relief="flat",font=("Cascadia Mono",9),padx=10,pady=6); self.mock_log.pack(fill="x",padx=12,pady=(0,12))

    def _spec(self): return RequestSpec(self.method.get(),self.url.get().strip(),parse_key_value_lines(self.params_text.get("1.0","end")),parse_key_value_lines(self.headers_text.get("1.0","end")),self.body_text.get("1.0","end-1c"))
    def _send(self):
        try: spec=self._spec()
        except RelayError as ex: messagebox.showerror("Relay",str(ex),parent=self); return
        self.summary.configure(text="Sending…")
        def work():
            try: result=perform_request(spec)
            except RelayError as ex: self.store.add_history(spec); self.after(0,lambda:self._show_error(str(ex))); return
            self.store.add_history(spec,result.status,result.elapsed_ms); self.after(0,lambda:self._show_result(result))
        threading.Thread(target=work,daemon=True).start()
    def _show_result(self,r):
        self._replace(self.response_text,r.body); self._replace(self.response_headers,"\n".join(f"{k}: {v}" for k,v in r.headers.items())); self.summary.configure(text=f"{r.status} {r.reason}  ·  {r.elapsed_ms:.0f} ms  ·  {r.size_bytes:,} B",foreground=GREEN if 200<=r.status<400 else RED); self._refresh_sidebar()
    def _show_error(self,e): self._replace(self.response_text,e); self.summary.configure(text=f"Request failed: {e}",foreground=RED); self._refresh_sidebar()
    def _save_request(self):
        try: spec=self._spec()
        except RelayError as ex: messagebox.showerror("Relay",str(ex),parent=self); return
        name=simpledialog.askstring("Save request","Name",initialvalue=f"{spec.method} {spec.url}",parent=self)
        if name: self.store.save_request(name,spec); self._refresh_sidebar()
    def _copy_curl(self):
        try: cmd=to_curl(self._spec())
        except RelayError as ex: messagebox.showerror("Relay",str(ex),parent=self); return
        self.clipboard_clear(); self.clipboard_append(cmd); self.summary.configure(text="cURL copied",foreground=ACCENT)
    def _refresh_sidebar(self):
        self.history_tree.delete(*self.history_tree.get_children()); self.saved_tree.delete(*self.saved_tree.get_children()); self._history_items=self.store.history(); self._saved_items=self.store.saved()
        for i,item in enumerate(self._history_items):
            req=item.get("request",{}); self.history_tree.insert("","end",iid=str(i),text=f"{req.get('method','GET')} {req.get('url','')}"[:45],values=(item.get("status") or "—",))
        for i,item in enumerate(self._saved_items): self.saved_tree.insert("","end",iid=str(i),text=str(item.get("name","Saved request"))[:48])
    def _apply_spec(self,spec):
        self.method.set(spec.method); self.url.set(spec.url); self._replace(self.params_text,"\n".join(f"{k}={v}" for k,v in spec.params.items())); self._replace(self.headers_text,"\n".join(f"{k}: {v}" for k,v in spec.headers.items())); self._replace(self.body_text,spec.body)
    @staticmethod
    def _replace(w,v): w.delete("1.0","end"); w.insert("1.0",v)
    def _load_history(self):
        s=self.history_tree.selection()
        if s:self._apply_spec(RequestSpec.from_dict(self._history_items[int(s[0])].get("request",{})))
    def _load_saved(self):
        s=self.saved_tree.selection()
        if s:self._apply_spec(RequestSpec.from_dict(self._saved_items[int(s[0])].get("request",{})))
    def _delete_saved(self):
        s=self.saved_tree.selection()
        if s:self.store.delete_saved(str(self._saved_items[int(s[0])].get("name",""))); self._refresh_sidebar()
    def _toggle_mock(self):
        if self.mock.running:self.mock.stop(); self.mock_button.configure(text="Start"); return
        try: self.mock.port=int(self.mock_port.get()); status=int(self.mock_status.get())
        except ValueError: messagebox.showerror("Relay","Port and status must be numbers.",parent=self); return
        self.mock.set_route(self.mock_path.get(),MockResponse(status=status,body=self.mock_body.get("1.0","end-1c")))
        try:self.mock.start()
        except OSError as ex:messagebox.showerror("Relay",f"Could not start mock server: {ex}",parent=self); return
        self.mock_button.configure(text="Stop"); self.url.set(f"http://127.0.0.1:{self.mock.port}{self.mock_path.get() or '/'}")
    def _mock_log(self,line): self.after(0,lambda:self._append_mock_log(line))
    def _append_mock_log(self,line): self.mock_log.insert("end",line+"\n"); self.mock_log.see("end")
    def _close(self): self.mock.stop(); self.destroy()

def main(): RelayApp().mainloop()
