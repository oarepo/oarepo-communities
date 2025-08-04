import React from "react";
import { useFormikContext, getIn } from "formik";
import { useFormConfig } from "@js/oarepo_ui";
import PropTypes from "prop-types";
import { i18next } from "@translations/oarepo_communities";
import { Message, Icon, Button, List } from "semantic-ui-react";
import { GenericCommunityMessage } from "./CommunitySelector";
import { CommunityItem } from "./CommunityItem";
import { Trans } from "react-i18next";
import { connect } from "react-redux";
import { changeSelectedCommunity } from "@js/oarepo_ui/forms/state/deposit/actions";

export const SelectedCommunityComponent = ({
  selectedCommunityId,
  selectCommunity,
  recordId,
}) => {
  const {
    formConfig: { allowed_communities, generic_community },
  } = useFormConfig();
  let selectedCommunity = allowed_communities.find(
    (c) => c.id === selectedCommunityId
  );
  const isGeneric = generic_community.id === selectedCommunityId;
  if (isGeneric) {
    selectedCommunity = generic_community;
  }
  const handleCommunityRemoval = () => {
    selectCommunity("");
  };
  return (
    <React.Fragment>
      {(recordId ||
        (selectedCommunityId && allowed_communities.length <= 1)) && (
        <p>
          {i18next.t(
            "Your record will be published in the following community:"
          )}
        </p>
      )}
      {!recordId && allowed_communities.length > 1 && selectedCommunity && (
        <Trans i18n={i18next}>
          Your work will be saved in the following community. Please note that
          after saving it will not be possible to transfer it to another
          community. Click
          <Button
            className="ml-5 mr-5"
            onClick={handleCommunityRemoval}
            size="mini"
          >
            here
          </Button>
          to change the selection.
        </Trans>
      )}
      {selectedCommunity && (
        <List>
          <CommunityItem community={selectedCommunity} />
        </List>
      )}
      {isGeneric ? (
        <Message>
          <Icon name="warning circle" className="text size large" />
          <GenericCommunityMessage />
        </Message>
      ) : null}
    </React.Fragment>
  );
};

SelectedCommunityComponent.propTypes = {
  fieldPath: PropTypes.string,
};

SelectedCommunityComponent.defaultProps = {
  fieldPath: "parent.communities.default",
};

const mapDispatchToProps = (dispatch) => ({
  selectCommunity: (communityId) =>
    dispatch(changeSelectedCommunity(communityId)),
});

const mapStateToProps = (state) => ({
  selectedCommunityId: state.deposit.record.parent.communities.default,
  recordId: state.deposit.record.id,
});

export const SelectedCommunity = connect(
  mapStateToProps,
  mapDispatchToProps
)(SelectedCommunityComponent);

export default SelectedCommunity;
