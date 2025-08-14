import React from "react";
import PropTypes from "prop-types";
import { Label, Icon } from "semantic-ui-react";

export const CommunityTypeLabel = ({ type, transparent = false }) => {
  if (type === undefined) return null;
  return (
    (transparent && (
      <div className="rel-mr-1">
        <Icon name="tag" />
        {type}
      </div>
    )) || (
      <Label size="small" horizontal className="primary">
        <Icon name="tag" />
        {type}
      </Label>
    )
  );
};

/* eslint-disable react/require-default-props */
CommunityTypeLabel.propTypes = {
  type: PropTypes.string,
  transparent: PropTypes.bool,
};
/* eslint-enable react/require-default-props */
