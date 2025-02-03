import { useQuery } from "@tanstack/react-query";
import React from "react";
import PropTypes from "prop-types";
import { httpApplicationJson } from "@js/oarepo_ui";
import { CommunityItem } from "@js/communities_components/CommunitySelector/CommunityItem";
import { List, Loader, Dimmer, Message } from "semantic-ui-react";
import { useFormikContext, getIn } from "formik";
import { i18next } from "@translations/oarepo_communities";

const SelectedTargetCommunity = ({ fieldPath, readOnlyLabel }) => {
  const { values } = useFormikContext();
  const selectedCommunityId = getIn(values, fieldPath, "");

  const { data, isFetching, isError } = useQuery(
    ["targetCommunity", selectedCommunityId],
    () => httpApplicationJson.get(`/api/communities/${selectedCommunityId}`),
    {
      enabled: !!selectedCommunityId,
      refetchOnWindowFocus: false,
      select: (data) => data.data,
    }
  );

  return (
    <React.Fragment>
      <strong>{readOnlyLabel}</strong>
      {isFetching ? (
        <Dimmer inverted active={isFetching}>
          <Loader active />
        </Dimmer>
      ) : (
        <List>
          {data && (
            <CommunityItem
              community={{
                id: data?.id,
                title: data?.metadata?.title,
                website: data?.metadata?.website,
                logo: data?.links?.logo,
                organizations: data?.metadata?.organizations,
                links: data?.links,
              }}
            />
          )}
        </List>
      )}
      {isError && (
        <Message negative>
          <Message.Content>
            {i18next.t("Could not fetch community.")}
          </Message.Content>
        </Message>
      )}
    </React.Fragment>
  );
};

SelectedTargetCommunity.propTypes = {
  fieldPath: PropTypes.string.isRequired,
  readOnlyLabel: PropTypes.string.isRequired,
};

export default SelectedTargetCommunity;
