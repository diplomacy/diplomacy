// ==============================================================================
// Copyright (C) 2019 - Philip Paquette, Steven Bocco
//
//  This program is free software: you can redistribute it and/or modify it under
//  the terms of the GNU Affero General Public License as published by the Free
//  Software Foundation, either version 3 of the License, or (at your option) any
//  later version.
//
//  This program is distributed in the hope that it will be useful, but WITHOUT
//  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
//  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
//  details.
//
//  You should have received a copy of the GNU Affero General Public License along
//  with this program.  If not, see <https://www.gnu.org/licenses/>.
// ==============================================================================
import React from 'react';
import PropTypes from 'prop-types';

export class Content extends React.Component {
    // PROPERTIES:
    // page: pointer to parent Page object
    // data: data for current content

    // Each derived class must implement this static method.
    static builder(page, data) {
        return {
            // page title (string)
            title: `${data ? 'with data' : 'without data'}`,
            // page navigation links: array of couples
            // (navigation title, navigation callback ( onClick=() => callback() ))
            navigation: [],
            // page content: React component (e.g. <MyComponent/>, or <div class="content">...</div>, etc).
            component: null
        };
    }

    getPage() {
        return this.props.page;
    }

    componentDidMount() {
        window.scrollTo(0, 0);
    }
}


Content.propTypes = {
    page: PropTypes.object.isRequired,
    data: PropTypes.object
};
