// Importing necessary libraries and widgets from Algolia
import algoliasearch from "algoliasearch/lite";
import instantsearch from "instantsearch.js";
import {
  configure,
  hits,
  pagination,
  panel,
  refinementList,
  numericMenu,
  searchBox,
  rangeSlider,
  toggleRefinement,
} from "instantsearch.js/es/widgets";

// Initializing the Algolia search client with your specific Application ID and Search-Only API Key
const searchClient = algoliasearch(
  "STSGRUJHZ7",
  "be53cd6c69c76ca67bbf313627929d90"
);

// Setting up the instant search configuration
const search = instantsearch({
  indexName: "products", // Using 'products' as the index name
  searchClient,
  insights: true, // Enabling insights for analytics
});

// Adding widgets to the search instance
search.addWidgets([
  searchBox({
    container: "#searchbox",
  }),
  hits({
    container: "#hits",
    templates: {
      item: (hit, { html, components }) => html`
        <article style="display: flex; align-items: center; gap: 20px;">
          <div
            style="flex-shrink: 0; width: 100px; height: 100px; background-size: cover; background-position: center; background-image: url('${hit.image}')"
          ></div>
          <div style="flex-grow: 1;">
            <h1>
              <a href="/products.html?pid=${hit.objectID}">
                ${components.Highlight({ hit, attribute: "name" })}
              </a>
            </h1>
            <p>${components.Highlight({ hit, attribute: "description" })}</p>
            <a href="/products.html?pid=${hit.objectID}">See product</a>
          </div>
        </article>
      `,
    },
  }),
  configure({
    hitsPerPage: 8,
  }),
  panel({
    templates: { header: "Brand" },
  })(refinementList)({
    container: "#brand-list",
    attribute: "brand",
  }),
  panel({
    templates: { header: "Categories" },
  })(refinementList)({
    container: "#category-list",
    attribute: "categories",
  }),
  toggleRefinement({
    container: "#free-shipping-toggle",
    attribute: "free_shipping",
    templates: {
      labelText: "Free Shipping",
    },
  }),
  panel({
    templates: { header: "Price Range" },
  })(numericMenu)({
    container: "#price-menu",
    attribute: "price",
    items: [
      { label: "All" },
      { label: "Under $50", end: 50 },
      { label: "$50 to $100", start: 50, end: 100 },
      { label: "$100 to $250", start: 100, end: 250 },
      { label: "Over $250", start: 250 },
    ],
  }),
  panel({
    templates: { header: "Rating" },
  })(rangeSlider)({
    container: "#rating-slider",
    attribute: "rating",
  }),
  pagination({
    container: "#pagination",
  }),
]);

// Starting the search
search.start();
