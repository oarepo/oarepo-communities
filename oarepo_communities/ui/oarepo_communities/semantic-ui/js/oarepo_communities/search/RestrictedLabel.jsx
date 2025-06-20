import { i18next } from "@translations/oarepo_dashboard";
import React from "react";

import { Label, Icon } from "semantic-ui-react";

export const RestrictedLabel = () => (
  <Label size="small" horizontal className="negative">
    <Icon name="ban" />
    {i18next.t("Restricted")}
  </Label>
);
