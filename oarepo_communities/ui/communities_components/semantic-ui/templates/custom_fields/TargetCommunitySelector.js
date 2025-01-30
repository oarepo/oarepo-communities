import React from "react";
import PropTypes from "prop-types";
import { SelectField } from "react-invenio-forms";
import { i18next } from "@translations/oarepo_communities";
import { CommunityItem } from "@js/communities_components/CommunitySelector/CommunityItem";
import { List } from "semantic-ui-react";
import { useFormikContext, getIn } from "formik";
import { search } from "@js/oarepo_ui/forms";

const serializeOptions = (options) =>
  options?.map((option) => ({
    text: option.title,
    value: option.id,
    key: option.id,
    name: option.title,
  }));

const TargetCommunitySelector = ({ fieldPath, allowedCommunities }) => {
  const { values } = useFormikContext();
  const selectedCommunityId = getIn(values, fieldPath, "");
  const selectedCommunity = allowedCommunities.find(
    (c) => c.id === selectedCommunityId
  );

  return (
    <React.Fragment>
      <SelectField
        fieldPath={fieldPath}
        options={serializeOptions(allowedCommunities)}
        multiple={false}
        required={true}
        label={i18next.t("Target community")}
        search={search}
        clearable
        searchInput={{
          autoFocus: true,
        }}
      />
      {selectedCommunity && (
        <List>
          <CommunityItem community={selectedCommunity} />
        </List>
      )}
    </React.Fragment>
  );
};

TargetCommunitySelector.propTypes = {
  fieldPath: PropTypes.string.isRequired,
  allowedCommunities: PropTypes.array.isRequired,
};

export default TargetCommunitySelector;
