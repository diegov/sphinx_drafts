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

        curr = self.state.document.get('preliminary_status')
        #If it's already "yes", we don't want to change it to "check"
        if curr == None or curr == 'check': 
            self.state.document['preliminary_status'] = self.arguments[0]
        return [preliminary_marker(check)]

#Debug methods

def print_node_attributes(node):
    print str(type(node)) + ' attribs: ' + str(dir(node))
    for attr_name in dir(node):
        if attr_name.startswith('_'): continue

        attr = getattr(node, attr_name)
        as_string = str(attr)

        print '       ' + attr_name + ': ' + as_string

def process(app, doctree, node_type):
    for node in doctree.traverse(node_type):
        print_node_attributes(node)

def print_node_tree(node, depth=0):
    msg = ' ' * depth * 4
    print msg + str(type(node))
    for child in node.children:
        print_node_tree(child, depth + 1)

#End of debug methods

def get_preliminary_references(app):
    env = app.builder.env
    if not hasattr(env, 'preliminary_references'):
        env.preliminary_references = []

    return env.preliminary_references

def process_preliminaries(app, doctree):
    references = get_preliminary_references(app)
    for node in doctree.traverse(sphinx.addnodes.pending_xref):
        print 'Attributes: ', str(node.attributes.keys())
        if 'reftarget' in node.attributes:
            reftarget = node.attributes['reftarget']
            print 'Ref target is %s, with type %s' % (reftarget, str(type(reftarget)))
            marker = refdoc_marker(reftarget)
            print 'Target of refdoc_marker just created', marker.target_doc
            doctree.append(marker)

def process_ref_nodes(app, doctree):
    # print '*************'
    # print 'doctree-read'
    # print '*************'
    #print_node_tree(doctree)
    #process(app, doctree, sphinx.addnodes.pending_xref)
    process_preliminaries(app, doctree)

def find_doc(app, doctree, doc_name):
    env = app.builder.env
    return env.get_doctree(doc_name)
    
def update_preliminary_status(app, doctree, seen_docs):
    curr = doctree.get('preliminary_status') 
    print ' * Initial status: %s' % (curr)
    print ' * Full doctree: %s' % (str(doctree))

    if curr == None: return 'no'
    if curr != 'check': return curr

    seen_docs.append(doctree)

    refs = doctree.get('preliminary_references')
    if not refs: return curr
    for dep_name in refs:
        print '    Processing ref %s' % (dep_name)
        dep = find_doc(app, doctree, dep_name)
        dep_status = dep.get('preliminary_status')
        if dep_status != None and dep_status == 'yes':
            return 'yes'

        if dep in seen_docs: continue

        if dep_status == 'check':
            dep['preliminary_status'] = update_preliminary_status(app, dep, seen_docs)

        print '          Finished processing ref %s, its status is %s' % (dep_name, dep['preliminary_status'])

        if dep_status == 'yes': return 'yes'

    return curr

def process_ref_nodes_resolved(app, doctree, docname):
    # print '****************'
    # print 'doctree-resolved'
    # print '****************'
    #process(app, doctree, nodes.reference)

    #print_node_attributes(doctree)
    
    print 'Doctree\'s preliminary status:', doctree.get('preliminary_status')

    doctree['preliminary_references'] = []
    for node in doctree.traverse(refdoc_marker):
        print 'Found reference:', node.target_doc
        doctree['preliminary_references'].append(node.target_doc)
        node.replace_self([])

    for node in doctree.traverse(preliminary_marker):
        if doctree['preliminary_status'] == 'check' and node.check:
            doctree['preliminary_status'] = \
                update_preliminary_status(app, doctree, [node])

        replacements = []
        if doctree['preliminary_status'] == 'yes':
            t = nodes.Text(preliminary_docs_text)
            p = nodes.paragraph()
            p.append(t)
            warning = nodes.warning()
            warning.append(p)
            replacements.append(warning)

        node.replace_self(replacements)
        
def setup(app):
    app.add_directive('preliminary', PreliminaryNote)
    app.connect('doctree-read', process_ref_nodes)
    app.connect('doctree-resolved', process_ref_nodes_resolved)
