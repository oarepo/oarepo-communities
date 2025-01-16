import { useQuery } from "@tanstack/react-query";
import React, { Component } from "react";
import PropTypes from "prop-types";
import { httpApplicationJson } from "@js/oarepo_ui";
import { SelectField } from "react-invenio-forms";
import { i18next } from "@translations/oarepo_communities";
import { CommunityItem } from "@js/communities_components/CommunitySelector/CommunityItem";
import { List } from "semantic-ui-react";
import { useFormikContext, getIn } from "formik";

const serializeOptions = (options) =>
  options?.map((option) => ({
    text: option.title,
    value: option.id,
    key: option.id,
  }));

const SelectedTargetCommunity = ({ requestType, fieldPath }) => {
  const { values } = useFormikContext();
  const selectedCommunityId = getIn(values, fieldPath, "");

  const { data, isLoading } = useQuery(
    ["targetCommunity", selectedCommunityId],
    () => httpApplicationJson.get(`/api/communities/${selectedCommunityId}`),
    {
      enabled: !!selectedCommunityId,
      refetchOnWindowFocus: false,
      staleTime: Infinity,
    }
  );
  const targetCommunity = data?.data;
  console.log(targetCommunity);

  return (
    <div>
      <div>Target community:</div>
      {!isLoading && (
        <List>
          <CommunityItem
            community={{
              id: targetCommunity.id,
              title: targetCommunity.metadata?.title,
              website: targetCommunity.metadata?.website,
              logo: targetCommunity.links?.logo,
              organizations: targetCommunity.metadata?.organizations,
              links: targetCommunity.links,
            }}
          />
        </List>
      )}
    </div>
  );
};

export default SelectedTargetCommunity;
