# sphinx-draft: a sphinx extension to mark pages as draft 
# and automatically mark referring pages as draft 
#
# Copyright (C) 2012 Diego Veralli <diegoveralli@yahoo.co.uk>
#
#  This file is part of sphinx-draft.
#  
#  sphinx-draft is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  sphinx-draft is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with sphinx-draft. If not, see <http://www.gnu.org/licenses/>.
#

from docutils import nodes
import sphinx
import inspect

from sphinx.locale import _
from sphinx.environment import NoUri
from sphinx.util.nodes import set_source_info
from sphinx.util.compat import Directive, make_admonition
from sphinx.util.compat import nodes

draft_docs_text = "This is draft documentation"

class refdoc_marker(nodes.General, nodes.Element): 
    def __init__(self, target_doc):
        super(refdoc_marker, self).__init__()
        self.target_doc = target_doc
        
class draft_marker(nodes.General, nodes.Element): 
    def __init__(self, check):
        super(draft_marker, self).__init__()
        self.check = check

class DraftNote(Directive):
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

        return [draft_marker(check)]

def get_draft_info(app, docname, doctree):
    env = app.builder.env
    if not hasattr(env, 'draft_doc_status'):
        env.draft_doc_status = {}

    if docname == None or not docname in env.draft_doc_status:
        retval = doctree.attributes.get('draft_info')
        if retval == None:
            retval = {}
            doctree.attributes['draft_info'] = retval

        if docname != None:
            env.draft_doc_status[docname] = retval
    else: retval = env.draft_doc_status[docname]
        
    return retval

def process_preliminaries(app, doctree):
    pre_info = get_draft_info(app, None, doctree)

    for node in doctree.traverse(draft_marker):
        curr = pre_info.get('draft_status')
        if curr == None or curr == 'check': 
            pre_info['draft_status'] = 'check' if node.check else 'yes'

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
    
def update_draft_status(app, doctree, docname, seen_docs):
    pre_info = get_draft_info(app, docname, doctree)
    curr = pre_info.get('draft_status') 

    if curr == None: return ('no', None)
    if curr != 'check': return (curr, pre_info.get('draft_dependencies'))

    seen_docs.append(docname)

    refs = pre_info.get('link_references')
    if refs == None:
        refs = []
        pre_info['link_references'] = refs

    for node in doctree.traverse(refdoc_marker):
        if node.target_doc not in refs:
            refs.append(node.target_doc)

    refs = pre_info.get('link_references')
    if not refs: return (curr, pre_info.get('link_references'))

    draft_dependencies = []
    for dep_name in refs:
        depname, dep = find_doc(app, docname, dep_name)
        dep_info = get_draft_info(app, depname, dep)
        dep_status = dep_info.get('draft_status')
        if dep_status != None and dep_status == 'yes':
            draft_dependencies.append(depname)

        if depname in seen_docs: continue

        if dep_status == 'check':
            status, dependencies = update_draft_status(app, dep, depname, seen_docs)
            dep_info['draft_status'] = status
            dep_info['draft_dependencies'] = dependencies

    if len(draft_dependencies) > 0:
        return ('yes', draft_dependencies)
    else: return (curr, pre_info.get('draft_dependencies'))

def create_draft_warning(draft_dependencies=None):
    text = draft_docs_text
    if draft_dependencies:
        text += " because it links to the following draft pages:"
    t = nodes.Text(text)
    p = nodes.paragraph()
    p.append(t)

    warning = nodes.warning()
    warning.append(p)
    if draft_dependencies:
        lst = nodes.bullet_list()
        for dep in draft_dependencies:
            item = nodes.list_item()
            item_p = nodes.paragraph()
            item_t = nodes.Text(dep)
            item_p.append(item_t)
            item.append(item_p)
            lst.append(item)

        warning.append(lst)
    return warning

def process_draft_nodes_resolved(app, doctree, docname):
    pre_info = get_draft_info(app, docname, doctree)

    for node in doctree.traverse(draft_marker):
        if pre_info['draft_status'] == 'check' and node.check:
            status, dependencies = update_draft_status(app, doctree, docname, [docname])
            pre_info['draft_status'] = status
            pre_info['draft_dependencies'] = dependencies

        replacements = []
        if pre_info['draft_status'] == 'yes':
            warning = create_draft_warning(pre_info.get('draft_dependencies'))
            replacements.append(warning)

        node.replace_self(replacements)

    for node in doctree.traverse(refdoc_marker):
        node.replace_self([])

def setup(app):
    app.add_directive('draft', DraftNote)
    app.connect('doctree-read', process_ref_nodes)
    app.connect('doctree-resolved', process_draft_nodes_resolved)

