import { useQuery } from "@tanstack/react-query";
import React from "react";
import PropTypes from "prop-types";
import { httpApplicationJson } from "@js/oarepo_ui";
import { CommunityItem } from "@js/communities_components/CommunitySelector/CommunityItem";
import { List } from "semantic-ui-react";
import { useFormikContext, getIn } from "formik";

const SelectedTargetCommunity = ({ fieldPath, readOnlyLabel }) => {
  const { values } = useFormikContext();
  const selectedCommunityId = getIn(values, fieldPath, "");

  const { data, isLoading } = useQuery(
    ["targetCommunity", selectedCommunityId],
    () => httpApplicationJson.get(`/api/communities/${selectedCommunityId}`),
    {
      enabled: !!selectedCommunityId,
      refetchOnWindowFocus: false,
      staleTime: Infinity,
      select: (data) => data.data,
    }
  );

  return (
    <React.Fragment>
      <strong>{readOnlyLabel}</strong>
      {!isLoading && (
        <List>
          <CommunityItem
            community={{
              id: data.id,
              title: data.metadata?.title,
              website: data.metadata?.website,
              logo: data.links?.logo,
              organizations: data.metadata?.organizations,
              links: data.links,
            }}
          />
        </List>
      )}
    </React.Fragment>
  );
};

SelectedTargetCommunity.propTypes = {
  fieldPath: PropTypes.string.isRequired,
  readOnlyLabel: PropTypes.string.isRequired,
};

export default SelectedTargetCommunity;
