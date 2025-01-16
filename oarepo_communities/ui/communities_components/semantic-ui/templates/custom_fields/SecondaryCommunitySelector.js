import PropTypes from "prop-types";
import { i18next } from "@translations/oarepo_communities";
import { CommunityItem } from "@js/communities_components/CommunitySelector/CommunityItem";
import { List } from "semantic-ui-react";
import { useFormikContext, getIn } from "formik";
import React, { useState } from "react";
import { OverridableContext } from "react-overridable";
import {
  EmptyResults,
  Error,
  InvenioSearchApi,
  ReactSearchKit,
  ResultsLoader,
  SearchBar,
  Pagination,
  withState,
} from "react-searchkit";
import { Grid, Menu, Message, Icon } from "semantic-ui-react";
import { EmptyResultsElement } from "@js/oarepo_ui";
const overriddenComponents = {
  "EmptyResults.element": EmptyResultsElement,
};

const searchConfig = {
  searchApi: {
    axios: {
      headers: {
        Accept: "application/vnd.inveniordm.v1+json",
      },
      url: "/api/communities",
    },
  },
  initialQueryState: {
    size: 5,
    page: 1,
    sortBy: "newest",
  },
};

const SecondaryCommunitySelector = ({ requestType, fieldPath }) => {
  const { values, errors, setFieldValue, setFieldError } = useFormikContext();
  console.log(errors);
  const selectedCommunityId = getIn(values, fieldPath, "");
  const [communityEndpoint, setCommunityEndpoint] = useState("all");
  const searchApiWithUrl = {
    ...searchConfig.searchApi,
    axios: {
      ...searchConfig.searchApi.axios,
      url:
        communityEndpoint === "all"
          ? "/api/communities"
          : "/api/user/communities",
    },
  };
  const searchApi = new InvenioSearchApi(searchApiWithUrl);

  const handleClick = (communityId) => {
    if (selectedCommunityId === communityId) return;
    setFieldValue(fieldPath, communityId);
    setFieldError(fieldPath, null);
  };

  return (
    <React.Fragment>
      <OverridableContext.Provider value={overriddenComponents}>
        <ReactSearchKit
          // necessary, because otherwise, when you switch tabs, it won't refetch
          key={communityEndpoint}
          searchApi={searchApi}
          urlHandlerApi={{ enabled: false }}
          initialQueryState={searchConfig.initialQueryState}
        >
          <Grid>
            <Grid.Row>
              <Grid.Column width={8} floated="left" verticalAlign="middle">
                <SearchBar
                  placeholder={i18next.t("Search")}
                  autofocus
                  actionProps={{
                    icon: "search",
                    content: null,
                    className: "search",
                  }}
                />
              </Grid.Column>
              <Grid.Column width={8} textAlign="right" floated="right">
                <Menu
                  compact
                  size="tiny"
                  className="license-toggler shadowless"
                >
                  <Menu.Item
                    content={i18next.t("All")}
                    name="all"
                    active={communityEndpoint === "all"}
                    onClick={() => setCommunityEndpoint("all")}
                  />
                  <Menu.Item
                    content={i18next.t("Mine")}
                    name="mine"
                    active={communityEndpoint === "mine"}
                    onClick={() => setCommunityEndpoint("mine")}
                  />
                </Menu>
              </Grid.Column>
            </Grid.Row>
            {getIn(errors, fieldPath, null) && (
              <Grid.Row>
                <Grid.Column width={16}>
                  <Message negative>
                    <Message.Content>
                      {getIn(errors, fieldPath)}
                    </Message.Content>
                  </Message>
                </Grid.Column>
              </Grid.Row>
            )}
            <Grid.Row verticalAlign="middle">
              <Grid.Column>
                <ResultsLoader>
                  <EmptyResults />
                  <Error />
                  <CommunityResults
                    handleClick={handleClick}
                    selectedCommunityId={selectedCommunityId}
                  />
                  <div className="centered">
                    <Pagination
                      options={{
                        size: "mini",
                        showFirst: false,
                        showLast: false,
                      }}
                      showWhenOnlyOnePage={false}
                    />
                  </div>
                </ResultsLoader>
              </Grid.Column>
            </Grid.Row>
          </Grid>
        </ReactSearchKit>
      </OverridableContext.Provider>
    </React.Fragment>
  );
};

export default SecondaryCommunitySelector;

export const CommunityResults = withState(
  ({ currentResultsState: results, handleClick, selectedCommunityId }) => {
    return (
      <List selection>
        {results.data.hits.map((result) => {
          const active = selectedCommunityId === result.id;
          return (
            <CommunityItem
              renderLinks={false}
              key={result.id}
              active={active}
              handleClick={handleClick}
              community={{
                id: result.id,
                title: result.metadata?.title,
                website: result.metadata?.website,
                logo: result.links?.logo,
                organizations: result.metadata?.organizations,
                links: result.links,
              }}
            />
          );
        })}
      </List>
    );
  }
);
