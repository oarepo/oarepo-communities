import { useQuery } from "@tanstack/react-query";
import React, { Component } from "react";
import PropTypes from "prop-types";
import { httpApplicationJson } from "@js/oarepo_ui";
import { SelectField } from "react-invenio-forms";
import { i18next } from "@translations/oarepo_communities";
import { CommunityItem } from "@js/communities_components/CommunitySelector/CommunityItem";
import { List, Dimmer, Loader } from "semantic-ui-react";
import { useFormikContext, getIn } from "formik";
import { search } from "@js/oarepo_vocabularies";

const serializeOptions = (options) =>
  options?.map((option) => ({
    text: option.title,
    value: option.id,
    key: option.id,
    name: option.title,
  }));

const TargetCommunitySelector = ({ requestType, fieldPath }) => {
  const { data, isLoading } = useQuery(
    ["formConfig", requestType],
    () => httpApplicationJson.get(`/requests/configs/${requestType}`),
    {
      enabled: !!requestType,
      refetchOnWindowFocus: false,
      staleTime: Infinity,
    }
  );
  const allowedCommunities = data?.data?.allowed_communities;
  const { values } = useFormikContext();
  const selectedCommunityId = getIn(values, fieldPath, "");

  return isLoading ? (
    <Dimmer active={isLoading} inverted>
      <Loader inverted active={isLoading} />
    </Dimmer>
  ) : (
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
      {selectedCommunityId && (
        <List>
          <CommunityItem
            community={allowedCommunities.find(
              (c) => c.id === selectedCommunityId
            )}
          />
        </List>
      )}
    </React.Fragment>
  );
};

export default TargetCommunitySelector;
