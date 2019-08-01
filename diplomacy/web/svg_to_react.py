# ==============================================================================
# Copyright (C) 2019 - Philip Paquette, Steven Bocco
#
#  This program is free software: you can redistribute it and/or modify it under
#  the terms of the GNU Affero General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
#  details.
#
#  You should have received a copy of the GNU Affero General Public License along
#  with this program.  If not, see <https://www.gnu.org/licenses/>.
# ==============================================================================
""" Helper script to convert a SVG file into a React JS component file.
    Type `python <script name> --help` for help.
"""
import argparse
import os
import sys
from xml.dom import minidom, Node

import ujson as json


def safe_react_attribute_name(name):
    """ Convert given raw attribute name into a valid React HTML tag attribute name.
        :param name: attribute to convert
        :return: valid attribute
        :type name: str
        :rtype: str
    """
    # Replace 'class' with 'className'
    if name == 'class':
        return 'className'
    # Replace aa-bb-cc with aaBbCc.
    if '-' in name:
        input_pieces = name.split('-')
        output_pieces = [input_pieces[0]]
        for piece in input_pieces[1:]:
            output_pieces.append('%s%s' % (piece[0].upper(), piece[1:]))
        return ''.join(output_pieces)
    # Otherwise, return name as-is.
    return name


def compact_extra(extra):
    """ Compact extra dictionary so that it takes less place into final output string.
        :param extra: dictionary of extra data
        :type extra: dict
    """
    if 'children' in extra:
        names = set()
        text_found = False
        for child in extra['children']:
            if isinstance(child, str):
                text_found = True
            else:
                names.add(child['name'])
        if len(names) == len(extra['children']):
            # Each child has a different name, so they cannot be confused, and extra dictionary can be merged with them.
            children_dict = {}
            for child in extra['children']:
                child_name = child.pop('name')
                compact_extra(child)
                children_dict[child_name] = child
            extra.pop('children')
            extra.update(children_dict)
        elif not text_found:
            # Classify children by name.
            classed = {}
            for child in extra['children']:
                classed.setdefault(child['name'], []).append(child)
            # Remove extra['children']
            extra.pop('children')
            for name, children in classed.items():
                if len(children) == 1:
                    # This child is the only one with that name. Merge it with extra dictionary.
                    child = children[0]
                    child.pop('name')
                    compact_extra(child)
                    extra[name] = child
                else:
                    # We found many children with same name. Merge them as a list into extra dictionary.
                    values = []
                    for child in children:
                        child.pop('name')
                        compact_extra(child)
                        values.append(child)
                    extra[name] = values
        else:
            for child in extra['children']:
                compact_extra(child)
    if 'attributes' in extra:
        if not extra['attributes']:
            extra.pop('attributes')
        elif 'name' not in extra or 'name' not in extra['attributes']:
            # Dictionary can be merged with its 'attributes' field.
            extra.update(extra.pop('attributes'))


def extract_extra(node, extra):
    """ Collect extra information from given node into output extra.
        :type extra: dict
    """
    extra_dictionary = {'name': node.tagName, 'attributes': {}, 'children': []}
    # Collect attributes.
    for attribute_index in range(node.attributes.length):
        attribute = node.attributes.item(attribute_index)
        extra_dictionary['attributes'][attribute.name] = attribute.value
    # Collect children lines.
    for child in node.childNodes:
        if child.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
            # Child is a text.
            text = child.data.strip()
            if text:
                extra_dictionary['children'].append(text)
        else:
            # Child is a normal node. We still consider it as an extra node.
            extract_extra(child, extra_dictionary)
    # Save extra node data into list field extra['children'].
    extra.setdefault('children', []).append(extra_dictionary)


def attributes_to_string(attributes):
    """ Convert given HTML attributes ton an inline string.
        :param attributes: attributes to write
        :return: a string representing attributes
        :type attributes: dict
        :rtype: str
    """
    pieces = []
    for name in sorted(attributes):
        value = attributes[name]
        if value.startswith('{'):
            pieces.append('%s=%s' % (name, value))
        else:
            pieces.append('%s="%s"' % (name, value))
    return ' '.join(pieces)


def extract_dom(node, nb_indentation, lines, extra, style_lines, id_to_class, identifiers_to_remove, action_parents):
    """ Parse given node.
        :param node: (input) node to parse
        :param nb_indentation: (input) number of indentation to use for current node content into output lines
            1 indentation is converted to 4 spaces.
        :param lines: (output) lines to collect output lines of text corresponding to parsed content
        :param extra: (output) dictionary to collect extra data (corresponding to invalid/unhandled tags(
        :param style_lines: (output) lines to collect output lines of CSS file corresponding to `style` tag (if found)
        :type nb_indentation: int
        :type lines: List[str]
        :type extra: dict
        :type style_lines: List[str]
        :type id_to_class: dict
        :type identifiers_to_remove: Iterable[str]
        :type action_parents: Iterable[str]
    """
    if node.nodeType != Node.ELEMENT_NODE:
        return
    tag_name = node.tagName
    if ':' in tag_name:
        # Found unhandled tag (example: `<jdipNS:DISPLAY>`). Collect it (and all its descendants) into extra.
        extract_extra(node, extra)
    else:
        # Found valid tag.
        attributes = {}
        child_lines = []
        node_id = None
        node_class = None
        # Collect attributes.
        for attribute_index in range(node.attributes.length):
            attribute = node.attributes.item(attribute_index)
            attribute_name = safe_react_attribute_name(attribute.name)
            # Attributes "xmlns:*" are not handled by React. Skip them.
            if not attribute_name.startswith('xmlns:') and attribute_name != 'version':
                attributes[attribute_name] = attribute.value
                if attribute_name == 'id':
                    node_id = attribute.value
                elif attribute_name == 'className':
                    node_class = attribute.value
        if node_id:
            if identifiers_to_remove and node_id in identifiers_to_remove:
                # This node must be skipped.
                return
            if node_class:
                # We parameterize class name for this node.
                attributes['className'] = "{classes['%s']}" % node_id
                id_to_class[node_id] = node_class
            if node.parentNode.getAttribute('id') in action_parents:
                # This node must react to onClick and onMouseOver.
                attributes['onClick'] = '{this.onClick}'
                attributes['onMouseOver'] = '{this.onHover}'
        # Collect children lines.
        for child in node.childNodes:
            if child.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
                # Found a text node.
                text = child.data.strip()
                if text:
                    child_lines.append(text)
            else:
                # Found an element node.
                extract_dom(child, nb_indentation + 1, child_lines, extra, style_lines,
                            id_to_class, identifiers_to_remove, action_parents)
        if tag_name == 'style':
            # Found 'style' tag. Save its children lines into style lines and return immediately,
            style_lines.extend(child_lines)
            return
        # We have a normal element node (not style node). Convert it to output lines.
        indentation = ' ' * (4 * nb_indentation)
        attributes_string = attributes_to_string(attributes)
        if child_lines:
            # Node must be written as an open tag.
            if len(child_lines) == 1:
                # If we just have 1 child line, write a compact line.
                lines.append(
                    '%s<%s%s>%s</%s>' % (
                        indentation, tag_name, (' %s' % attributes_string) if attributes_string else '',
                        child_lines[0].lstrip(),
                        tag_name))
            else:
                # Otherwise, write node normally.
                lines.append(
                    '%s<%s%s>' % (indentation, tag_name, (' %s' % attributes_string) if attributes_string else ''))
                lines.extend(child_lines)
                lines.append('%s</%s>' % (indentation, tag_name))
        else:
            # Node can be written as a close tag.
            lines.append(
                '%s<%s%s/>' % (indentation, tag_name, (' %s' % attributes_string) if attributes_string else ''))


def main():
    """ Main script function. """
    parser = argparse.ArgumentParser(
        prog='Convert a SVG file to a React Component.'
    )
    parser.add_argument('--input', '-i', type=str, required=True, help='SVG file to convert.')
    parser.add_argument('--name', '-n', type=str, required=True, help="Component name.")
    parser.add_argument('--output', '-o', type=str, default=os.getcwd(),
                        help='Output folder (default to working folder).')
    parser.add_argument('--remove', '-r', action='append', help='(optional) Identifiers of nodes to remove')
    parser.add_argument('--actionable', '-a', action='append',
                        help='(optional) Identifiers for which '
                             'all immediate children must have onClick and onMouseOver.')
    args = parser.parse_args()
    root = minidom.parse(args.input).documentElement
    class_name = args.name
    output_folder = args.output
    identifiers_to_remove = set(args.remove) if args.remove else set()
    action_parents = set(args.actionable) if args.actionable else set()
    assert os.path.isdir(output_folder), 'Not a directory: %s' % output_folder
    extra_class_name = '%sExtra' % class_name
    lines = []
    extra = {}
    style_lines = []
    id_to_class = {}
    extract_dom(root, 3, lines, extra, style_lines, id_to_class, identifiers_to_remove, action_parents)
    compact_extra(extra)

    output_file_name = os.path.join(output_folder, '%s.js' % class_name)
    style_file_name = os.path.join(output_folder, '%s.css' % class_name)
    extra_file_name = os.path.join(output_folder, '%s.js' % extra_class_name)

    if style_lines:
        with open(style_file_name, 'w') as style_file:
            style_file.writelines(style_lines)

    if extra:
        with open(extra_file_name, 'w') as extra_file:
            extra_file.write("""export const %(extra_class_name)s = %(extra_content)s;""" % {
                'extra_class_name': extra_class_name,
                'extra_content': json.dumps(extra, indent=4)
            })

    with open(output_file_name, 'w') as file:
        file.write("""/** Generated using %(program_name)s with parameters:
%(args)s
**/
import React from 'react';
import PropTypes from 'prop-types';
%(style_content)s
%(extra_content)s

function getClickedID(event) {
    let node = event.target;
    if (!node.id && node.parentNode.id && node.parentNode.tagName === 'g')
        node = node.parentNode;
    return node.id;
}

export class %(classname)s extends React.Component {
    constructor(props) {
        super(props);
        this.onClick = this.onClick.bind(this);
        this.onHover = this.onHover.bind(this);
    }
    onClick(event) {
        if (this.props.onClick) {
            const id = getClickedID(event);
            if (id) {
                this.props.onClick(id);
            }
        }
    }
    onHover(event) {
        if (this.props.onHover) {
            const id = getClickedID(event);
            if (id) {
                this.props.onHover(id);
            }
        }
    }
    render() {
        const classes = %(classes)s;
        return (
%(svg)s
        );
    }
}
%(classname)s.propTypes = {
    onHover: PropTypes.func
};
""" % {
    'style_content': "import './%s.css';" % class_name if style_lines else '',
    'extra_content': "import {%s} from './%s';" % (extra_class_name, extra_class_name) if extra else '',
    'classname': class_name,
    'classes': json.dumps(id_to_class),
    'svg': '\n'.join(lines),
    'program_name': sys.argv[0],
    'args': args
})


if __name__ == '__main__':
    main()
