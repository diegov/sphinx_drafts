from docutils import nodes
import sphinx
import inspect

from sphinx.locale import _
from sphinx.environment import NoUri
from sphinx.util.nodes import set_source_info
from sphinx.util.compat import Directive, make_admonition
from sphinx.util.compat import nodes

preliminary_docs_text = "This is preliminary documentation"

class refdoc_marker(nodes.General, nodes.Element): 
    def __init__(self, target_doc):
        super(refdoc_marker, self).__init__()
        self.target_doc = target_doc
        
class preliminary_marker(nodes.General, nodes.Element): 
    def __init__(self, check):
        super(preliminary_marker, self).__init__()
        self.check = check

class PreliminaryNote(Directive):
    has_content = False
    required_arguments = 1

    def run(self):
        if self.arguments[0] == 'yes':
            check = False
        elif self.arguments[0] == 'check':
            check = True
        else: 
            msg = 'Argument must be "yes" or "check", found "%s" instead' % \
                self.arguments[0]
            raise Exception, msg

        return [preliminary_marker(check)]

def get_preliminary_info(app, docname, doctree):
    env = app.builder.env
    if not hasattr(env, 'preliminary_doc_status'):
        env.preliminary_doc_status = {}

    if docname == None or not docname in env.preliminary_doc_status:
        retval = doctree.attributes.get('preliminary_info')
        if retval == None:
            retval = {}
            doctree.attributes['preliminary_info'] = retval

        if docname != None:
            env.preliminary_doc_status[docname] = retval
    else: retval = env.preliminary_doc_status[docname]
        
    return retval

def process_preliminaries(app, doctree):
    pre_info = get_preliminary_info(app, None, doctree)

    for node in doctree.traverse(preliminary_marker):
        curr = pre_info.get('preliminary_status')
        if curr == None or curr == 'check': 
            pre_info['preliminary_status'] = 'check' if node.check else 'yes'

    for node in doctree.traverse(sphinx.addnodes.pending_xref):
        if 'reftarget' in node.attributes:
            reftarget = node.attributes['reftarget']
            marker = refdoc_marker(reftarget)
            doctree.append(marker)

def process_ref_nodes(app, doctree):
    process_preliminaries(app, doctree)

def locate_relative_doc(refdoc_name, doc_name):
    if doc_name.startswith('/'): return doc_name
    elif '/' in refdoc_name:
        split_point = refdoc_name.rindex('/')
        return refdoc_name[:split_point + 1] + doc_name

    return doc_name

def find_doc(app, refdoc_name, doc_name):
    env = app.builder.env
    name = locate_relative_doc(refdoc_name, doc_name)
    return (name, env.get_doctree(name))
    
def update_preliminary_status(app, doctree, docname, seen_docs):
    pre_info = get_preliminary_info(app, docname, doctree)
    curr = pre_info.get('preliminary_status') 

    if curr == None: return 'no'
    if curr != 'check': return curr

    seen_docs.append(docname)

    refs = pre_info.get('preliminary_references')
    if refs == None:
        refs = []
        pre_info['preliminary_references'] = refs

    for node in doctree.traverse(refdoc_marker):
        if node.target_doc not in refs:
            refs.append(node.target_doc)

    refs = pre_info.get('preliminary_references')
    if not refs: return curr
    for dep_name in refs:
        depname, dep = find_doc(app, docname, dep_name)
        dep_info = get_preliminary_info(app, depname, dep)
        dep_status = dep_info.get('preliminary_status')
        if dep_status != None and dep_status == 'yes':
            return 'yes'

        if depname in seen_docs: continue

        if dep_status == 'check':
            dep_info['preliminary_status'] = \
                update_preliminary_status(app, dep, depname, seen_docs)

        if dep_status == 'yes': return 'yes'

    return curr

def create_preliminary_warning():
    t = nodes.Text(preliminary_docs_text)
    p = nodes.paragraph()
    p.append(t)
    warning = nodes.warning()
    warning.append(p)
    return warning

def process_preliminary_nodes_resolved(app, doctree, docname):
    pre_info = get_preliminary_info(app, docname, doctree)

    for node in doctree.traverse(preliminary_marker):
        if pre_info['preliminary_status'] == 'check' and node.check:
            pre_info['preliminary_status'] = \
                update_preliminary_status(app, doctree, docname, [docname])

        replacements = []
        if pre_info['preliminary_status'] == 'yes':
            warning = create_preliminary_warning()
            replacements.append(warning)

        node.replace_self(replacements)

    for node in doctree.traverse(refdoc_marker):
        node.replace_self([])

def setup(app):
    app.add_directive('preliminary', PreliminaryNote)
    app.connect('doctree-read', process_ref_nodes)
    app.connect('doctree-resolved', process_preliminary_nodes_resolved)

